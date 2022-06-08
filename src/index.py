# Invoke describe/get/list APIs using HTTP Get method from web clients (usually
# web browsers) and relay outputs back to the clients
# The function behaves as a proxy (AWS API proxy)

import json
import boto3
import re
import os
from datetime import datetime, timedelta, timezone

s3 = boto3.resource('s3')
S3_BUCKET = os.getenv('s3_bucket') or ''

ERR_MSG_KEY = 'Error_Message'

def access_permission(event):

    if not isinstance(event.get('requestContext', {}).get('http', {}).get('sourceIp'), str):
       return 'Access Denied'

    for ip_prefix in os.getenv('source_ip_prefix_list').split(' '):
       if event['requestContext']['http']['sourceIp'].startswith(ip_prefix):
           # OK
           return None

    # NG
    return 'Access Denied'

def url_param_validator(params):

    global S3_BUCKET

    # Error. No 'api=' Parameter
    if not isinstance(params, dict) or params.get('api') == None:
        return None, 'Bad Request'

    # Error. Parameter 'api=<namespace>:<API(readonly)>' is invalid
    if re.match(r'[a-z][a-z0-9_\-]{1,32}\:(describe|list|get)_[a-z0-9_]{1,60}$', params['api']) == None:
        return None, 'invalid api parameter.  OK example: api=ec2:describe_subnets'

    # region
    params.setdefault('region', (os.getenv('def_param_region') or 'ap-northeast-1'))

    # cache
    if params.get('cache') == 'never':
        S3_BUCKET = ''
    elif params.get('cache', '').isdigit():
        params['cache'] = str( max(1, int(params['cache'][0:9])) )
    else:
        params['cache'] = (os.getenv('def_param_cache') or '3600')

    return params, None

def create_s3obj_fullpath(params):

    fullname_pre = 'cache/' + params['region'] + '/' + params['api'].replace(':', '-')

    # For S3 object
    # argkey has printable characters only
    argkey = '_' + re.sub(r'[^\u0020-\u007E]', '', params.get('arg', ''))

    if len(argkey) > 1:
        fullname_pre += argkey

    return fullname_pre + '.json'

def get_s3_content_and_timestamp_if_exists(s3obj_fullname, cache):

    try:
        s3response = s3.Object(S3_BUCKET, s3obj_fullname).get()

        body = json.loads(s3response['Body'].read())
        last_modified = s3response.get('LastModified', None)

    except Exception:

        body = None
        last_modified = None

    return body, last_modified

def customize_content_before_s3put(content, params):

    # URL parameter has "api=cloudwatch:get_metric_widget_image"
    # Before :  { "MetricWidgetImage" : [ "b'\\x89PNG\\r\\n\\x1a  ...(snip)... " ] }
    # After  :  { "MetricWidgetImage" : "iVBORw0K  ...(snip)... " }
    if params['api'] == 'cloudwatch:get_metric_widget_image' and content.get('MetricWidgetImage'):
        import base64
        content['MetricWidgetImage'] = base64.b64encode(content['MetricWidgetImage']).decode()

    return content

def customize_content_after_s3put(content, params):

    # URL parameter has both "api=ec2:describe_instances" and "flatten"
    # Before :  { "Reservations" : [ { "Instances" : [ <EC2_A> ] }, { "Instances" : [ <EC2_B>, <EC2_C> ] } ] }
    # After  :  { "Instances" : [ <EC2_A>, <EC2_B>, <EC2_C> ] }
    if params['api'] == 'ec2:describe_instances' and params.get('flatten') != None:
        content = {
            'Instances' : sum( [ reservation['Instances'] for reservation in content.get('Reservations') ], [] )
        }

    return content

def filter_data_by_select_keys(data, select_keys):

    if not isinstance(data, dict) or len(data.keys()) != 1 or select_keys == ['']:
        return data

    data_key = list(data.keys())[0]

    if not isinstance(data[data_key], list):
        return data

    new_d = data[data_key].copy()

    for index, d in enumerate(data[data_key]):

        new_d[index] = {}
        for sel_key in select_keys:

            # Example) filter by "Id:Status"
            #   Before [ { "Id" : "v1", "Status" : "Ok", "Type" : "large" }, { "Id" : "v2", Status" : "Failed", "Type" : "small" } ]
            #   After  [ { "Id" : "v1", "Status" : "Ok" }, { "Id" : "v2", "Status" : "Failed" } ]
            if d.get(sel_key) != None:
                new_d[index][sel_key] = d[sel_key]

            # Example) Before filter by "Id:State.Name":
            #   Before [ { "Id" : "v1", "State" : { "Code" : 16, "Name": "running" } } ]
            #   After  [ { "Id" : "v1", "State.Name" : "running" } ]
            elif '.' in sel_key:
                dot_split = sel_key.split('.')
                if len(dot_split) == 2 and d.get(dot_split[0]) != None and isinstance(d[ dot_split[0] ], dict) and d[ dot_split[0] ].get(dot_split[1]) != None:
                    new_d[index][sel_key] = d[ dot_split[0] ][ dot_split[1] ]

    return { data_key : new_d }

def return_to_client(body, http_code=200, modified_time=None, content_type='application/json'):

    ret_headers = {
        'Content-Type': content_type + ';charset=utf-8'
    }

    if isinstance(modified_time, datetime):
        ret_headers['Last-Modified'] = modified_time.strftime('%a, %d %b %Y %H:%M:%S GMT')

    return {
        'isBase64Encoded': False,
        'statusCode': http_code,
        'headers': ret_headers,
        'body': body
    }

def lambda_handler(event, context):

    return_opt = { 'http_code' : 400 }

    access_err = access_permission(event)

    if access_err:
        # NG (HTTP 400 : Bad Request)
        return return_to_client({ ERR_MSG_KEY : str(access_err) }, **return_opt)

    params, param_err = url_param_validator(event.get('queryStringParameters'))

    if param_err:
        # NG (HTTP 400 : Bad Request)
        return return_to_client({ ERR_MSG_KEY : str(param_err) }, **return_opt)

    content, cache_datetime = None, None
    if S3_BUCKET != '':
        content, cache_datetime = get_s3_content_and_timestamp_if_exists( create_s3obj_fullpath(params), params.get('cache') )

    indent = int(params['indent']) if params.get('indent', '').isdigit() and int(params['indent']) in range(0, 64) else -1

    select_keys = params.get('select', '').split(':')

    if content != None and cache_datetime > datetime.now(timezone.utc) - timedelta(seconds=int(params['cache'])):
        # valid cache found

        return_opt['modified_time'] = cache_datetime

    else:
        # No cache or cache expired

        from botocore.exceptions import ClientError

        content = {}
        api_failed = False

        try:
            arg = json.loads( params.get('arg') or '{}' )

        except Exception as e:
            # NG (HTTP 400)
            return return_to_client({ 'Error Message': 'parameter arg decode error' }, **return_opt)
    
        try:
            ns_obj = boto3.client(params['api'].split(':')[0], region_name=params['region'])
            can_paginate = ns_obj.can_paginate(params['api'].split(':')[1])
    
        except Exception as e:
            # NG (HTTP 400)
            return return_to_client({ ERR_MSG_KEY : str(e) }, **return_opt)

        return_opt['modified_time'] = datetime.now(timezone.utc)

        try:
            if can_paginate:
                # Pagination API

                for func_out in ns_obj.get_paginator(params['api'].split(':')[1]).paginate(**arg):

                    for k in func_out.keys():

                        if k not in ['ResponseMetadata', 'Marker', 'NextToken', 'IsTruncated']:
                            content.setdefault(k, []).extend(func_out[k])

            else:
                # No Pagination API

                # AWS API
                func = eval('boto3.client(\'' + params['api'].split(':')[0] + '\', region_name=\'' + params['region'] + '\').' + params['api'].split(':')[1])
                content = func(**arg)

                if isinstance(content, dict):
                    content.pop('ResponseMetadata', None)

                print(content)

            if api_failed:
                # NG (HTTP 400)
                return return_to_client(content, **return_opt)
            else:
                content = customize_content_before_s3put(content, params)

        except ClientError as e:
            api_failed = True
            content = { ERR_MSG_KEY : e.response['Error'] }
        
        except Exception as e:
            api_failed = True
            content = { ERR_MSG_KEY : format(e) }

        if S3_BUCKET != '':
            s3.Object(S3_BUCKET, create_s3obj_fullpath(params)).put(
                Body = json.dumps(content, ensure_ascii=False, default=str)
            )

    return_opt['http_code'] = 200

    content = customize_content_after_s3put(content, params)

    # filter by URL parameter 'select='
    content = filter_data_by_select_keys(content, select_keys)

    if not indent >= 0:
        ret_body = json.dumps(content, ensure_ascii=False, default=str)
        return_opt['content_type'] = 'application/json'
    else:
        ret_body = '<!DOCTYPE html><pre>' + json.dumps(content, ensure_ascii=False, default=str, indent=indent) + '</pre>'
        return_opt['content_type'] = 'text/html'

    if len(ret_body) > 5.5 * 1024 * 1024:
        return_opt = { 'http_code' : 413, 'content_type' : 'application/json' }
        ret_body = json.dumps({ ERR_MSG_KEY : 'The size of your request exceeds the content size limit.' })

    return return_to_client(ret_body, **return_opt)
