# aws-lambda-describe-api

Invoke AWS read APIs (**describe_xxxx, get_xxxx or list_xxxx**) using HTTP Get method from web clients (usually web browsers) and relay outputs back to the clients.

This is a python code for AWS lambda function.

It behaves as a proxy (AWS API proxy).

<br>

## Flow Diagram

![aws-describe-api flod diagram](image/aws-describe-api_drawio.png)

1. Access from a web client to Lambda. (with API gateway or Lambda functions URLs)
2. Invoke AWS API included in URL parameters.
3. The web client gets JSON responses.

<br>

## Examples

Get List of AZs(Availability Zones)

- request URL

```
https://xxxxxxxxxxxxx.lambda-url.ap-northeast-1.on.aws/?api=ec2:describe_availability_zones&select=ZoneName:ZoneId&indent=4
```

- response

```
{
    "AvailabilityZones": [
        {
            "ZoneName": "ap-northeast-1a",
            "ZoneId": "apne1-az4"
        },
        {
            "ZoneName": "ap-northeast-1c",
            "ZoneId": "apne1-az1"
        },
        {
            "ZoneName": "ap-northeast-1d",
            "ZoneId": "apne1-az2"
        }
    ]
}
```

<br>

## Advantages compared to normal AWS API

- You don't have to pay attention to pagination (Lambda returns concatinated JSON pagenated results)
- ```select=element``` select a single element or some elements (example above)
- ```indent=n``` HTML style option instead of default JSON style
- ```region=us-east-1``` specific region option instead of default region
- Use S3 bucket as cache
- ```cache=n``` option expiration time in seconds 
- ```simpletag=Tags``` option convert complex tags to simple tags
- ```flatten``` option is enabled only when  ```ec2:describe_instances``` called
- Get Base64 PNG graphic data only when ```cloudwatch:get_metric_widget_image``` called

## Installation

Use AWS CloudFormation template.

[cfn_lambda-describe-api.yaml](src/cfn_lambda-describe-api.yaml)
