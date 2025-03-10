# Invoke describe/get/list APIs using HTTP GET method from web clients (usually
# web browsers) and relay the outputs back to the clients.
# This function acts as a proxy (AWS API proxy).

# Required IAM policies: ReadOnlyAccess, AWSLambdaBasicExecutionRole
# Desired IAM policy: AmazonS3FullAccess (or your custom S3 policy)

# Sample Test Event JSON
'''
{
    "requestContext": {
        "http": {
            "sourceIp": "12.34.56.78"
        }
    },
    "queryStringParameters": {
        "api": "ec2:describe_network_interfaces",
        "select": "NetworkInterfaceId:PrivateIpAddresses..PrivateIpAddress",
        "cache": "600"
    }
}
'''

import json
import re
import os
import ipaddress
from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import ClientError

s3 = boto3.resource('s3')
S3_BUCKET = os.getenv('s3_bucket', '')

session = boto3.Session()

ERR_MSG_KEY = 'Error_Message'
REMOVE_KEY_LIST = os.getenv('remove_key_list', 'ResponseMetadata Marker NextToken nextToken IsTruncated MaxResults')
MAX_BODY_SIZE = 6029312 # 5.75 MiB

def access_permission(request_context):
    """Check if the request source IP is allowed."""

    source_ip = request_context.get('http', {}).get('sourceIp', '')
    allowed_cidrs = os.getenv('source_cidr_list', '0.0.0.0/0 ::/0')

    for allowed_cidr in re.split(r'[, ]+', allowed_cidrs):
        if ipaddress.ip_address(source_ip) in ipaddress.ip_network(allowed_cidr):
            # OK
            return None

    return 'Access Denied'

def validate_url_params(params):
    """Validate URL parameters and set defaults."""

    if not isinstance(params, dict) or 'api' not in params:
        return None, 'Bad Request'

    if not re.match(r'[a-z][a-z0-9_\-]{1,32}\:(describe|list|get)_[a-z0-9_]{1,60}$', params['api']):
        return None, 'Invalid api parameter. example: api=ec2:describe_subnets'

    params.setdefault('region', os.getenv('default_region', 'us-east-1'))

    global S3_BUCKET
    if params.get('cache') == 'never':
        S3_BUCKET = ''
    elif params.get('cache', '').isdigit():
        params['cache'] = str(max(1, int(params['cache'][:9])))
    else:
        params['cache'] = os.getenv('default_cache', '60')

    return params, None

def build_s3_key(params):
    """Build S3 key for caching."""

    key_prefix = f"cache/{params['region']}/{params['api'].replace(':', '-')}"
    arg_key = '_' + re.sub(r'[^\u0020-\u007E]', '', params.get('arg', ''))

    return f"{key_prefix}{arg_key if len(arg_key) >= 2 else ''}.json"

def get_s3_cached_data(s3obj_fullname):
    """Retrieve cached data from S3 if it exists."""
    try:
        s3response = s3.Object(S3_BUCKET, s3obj_fullname).get()

        body = json.loads(s3response['Body'].read())
        last_modified = s3response.get('LastModified', None)

    except Exception:
        body = None
        last_modified = None

    return body, last_modified

def encode_metric_widget_image(content, params):
    """Encode CloudWatch MetricWidgetImage to Base64."""

    # Before: { "MetricWidgetImage": [ "b'\\x89PNG\\r\\n\\x1a ... (Binary data not encoded in Base64) " ] }
    # After : { "MetricWidgetImage": "iVBORw0K ... (Base64 encoded string) " }
    if params['api'] == 'cloudwatch:get_metric_widget_image' and content.get('MetricWidgetImage'):
        import base64
        content['MetricWidgetImage'] = base64.b64encode(content['MetricWidgetImage']).decode()
    return content

def flatten_ec2_instances(content, params):
    """Flatten EC2 instances if 'flatten' parameter is present."""

    # Before: { "Reservations" : [ { "Instances" : [ <EC2_A> ] }, { "Instances" : [ <EC2_B>, <EC2_C> ] } ] }
    # After : { "Instances" : [ <EC2_A>, <EC2_B>, <EC2_C> ] }
    if params['api'] == 'ec2:describe_instances' and params.get('flatten') is not None:
        content = {
            'Instances': sum(
                [res.get('Instances', []) for res in content.get('Reservations', [])], []
            )
        }
    return content

def simpletag_to_dict(content, params):
    """Convert Tags or TagList to simple key-value pairs."""

    if not (params.get('simpletag') is not None and isinstance(content, dict) and len(content) >= 1 and isinstance(list(content.values())[0], list)):
        return content

    # Before: [ { "Key": "Name", "Value": "Server1" }, { "Key": "Env", "Value": "Prod" } ]
    # After : { "Name": "Server1", "Env": "Prod" }
    for item in list(content.values())[0]:
        for tag_key in ['Tags', 'TagList']:
            if tag_key not in item:
                continue
            item[ tag_key ] = {
                x['Key']: x['Value'] for x in item[ tag_key ]
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

            if sel_key.count('.') <= 6:
                part_data = select_partial_data(sel_key, d)
                if part_data:
                    new_d[index][sel_key] = part_data

    return { data_key : new_d }

def select_partial_data(sel_key, d):
    """Extract partial data from nested dictionaries or lists using a dot-separated key."""

    sel_key_split = sel_key.split('.', 1)
    part_d = None

    if len(sel_key_split) == 1:
        if isinstance(d, dict):
            return d.get(sel_key)
        return None

    next_sel_key = sel_key_split[1]

    if len(sel_key_split[0]) == 0:
        if isinstance(d, list):
            part_d = []
            for d_each in d:
                part_d.append( select_partial_data(next_sel_key, d_each) )

            if len(part_d) >= 1 and not any(part_d):
                part_d = None
    else:
        if isinstance(d, dict):
            in_d = d.get( sel_key_split[0] )
            if in_d:
                part_d = select_partial_data(next_sel_key, in_d)

    return part_d

def return_to_client(body, http_code=200, modified_time=None, cache_sec=60):

    ret_headers = {
        'Content-Type': 'application/json;charset=utf-8',
        'Cache-Control': f'max-age={cache_sec}'
    }

    if isinstance(modified_time, datetime):
        ret_headers['Last-Modified'] = modified_time.strftime('%a, %d %b %Y %H:%M:%S GMT')

    return {
        'isBase64Encoded': False,
        'statusCode': http_code,
        'headers': ret_headers,
        'body': body
    }

def call_aws_api(api_service, api_method, region, **kwargs):

    client = session.client(api_service, region_name=region)
    method_to_call = getattr(client, api_method)
    return method_to_call(**kwargs)

def handle_api_request(params):

    content, cache_datetime = None, None
    modified_time = datetime.now(timezone.utc)

    if S3_BUCKET != '':
        content, cache_datetime = get_s3_cached_data( build_s3_key(params) )

    cache_sec = min(max(1, int(params['cache'])), 604800) if re.match('^[0-9]+', params['cache']) else 60

    if content is not None and cache_datetime > datetime.now(timezone.utc) - timedelta(seconds=cache_sec):
        modified_time = cache_datetime

    else:
        # No cache or cache expired

        content = {}
        api_method = params['api'].split(':')

        try:
            kwargs = json.loads( params.get('arg') or '{}' )
        except Exception:
            return None, None, None, 'Failed to decode parameter \'arg\''

        try:
            client = session.client(api_method[0], region_name=params['region'])
            can_paginate = client.can_paginate(api_method[1])
        except Exception as e:
            return None, None, None, f'{e} probably incorrect'

        try:
            if can_paginate:
                paginator = client.get_paginator(api_method[1])
                for func_output in paginator.paginate(**kwargs):
                    for k in func_output.keys():
                        if k not in REMOVE_KEY_LIST.split(' '):
                            content.setdefault(k, []).extend(func_output[k])

            else: # Pagination unsupported API

                content = call_aws_api(api_method[0], api_method[1], params['region'], **kwargs)
                if isinstance(content, dict):
                    content.pop('ResponseMetadata', None)

            content = encode_metric_widget_image(content, params)

        except ClientError as e:
            return None, None, None, e.response['Error']

        except Exception as e:
            return None, None, None, format(e)

        if S3_BUCKET != '':
            s3.Object(S3_BUCKET, build_s3_key(params)).put(
                Body = json.dumps(content, ensure_ascii=False, default=str)
            )

    return content, modified_time, cache_sec, None

def lambda_handler(event, context):

    return_opt = { 'http_code': 400 }

    try:
        access_err_message = access_permission(event.get('requestContext', {}))
    except Exception:
        access_err_message = 'Access Denied'

    if access_err_message:
        return return_to_client({ ERR_MSG_KEY : access_err_message }, **return_opt)

    params, param_err = validate_url_params(event.get('queryStringParameters'))

    if param_err:
        return return_to_client({ ERR_MSG_KEY : param_err }, **return_opt)

    select_keys = params.get('select', '').split(':')

    content, modified_time, cache_sec, failed_message = handle_api_request(params)

    if failed_message:
        return return_to_client({ ERR_MSG_KEY : failed_message }, **return_opt)

    return_opt.update({
        'http_code': 200,
        'modified_time': modified_time,
        'cache_sec': cache_sec
    })

    content = flatten_ec2_instances(content, params)
    content = simpletag_to_dict(content, params)

    content = filter_data_by_select_keys(content, select_keys)

    ret_body = json.dumps(content, ensure_ascii=False, default=str)

    if len(ret_body) > MAX_BODY_SIZE:
        return_opt = {'http_code': 413}
        ret_body = json.dumps({ERR_MSG_KEY: 'Content size limit exceeded.'})

    return return_to_client(ret_body, **return_opt)
