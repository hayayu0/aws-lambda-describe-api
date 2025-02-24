# aws-lambda-describe-api examples

## ✅ OK Case

---

**?api=ec2:describe_availability_zones&region=ap-northeast-1**

```json
{
  "AvailabilityZones": [
    {
      "State": "available",
      "OptInStatus": "opt-in-not-required",
      "Messages": [],
      "RegionName": "ap-northeast-1",
      "ZoneName": "ap-northeast-1a",
      "ZoneId": "apne1-az4",
      "GroupName": "ap-northeast-1",
      "NetworkBorderGroup": "ap-northeast-1",
      "ZoneType": "availability-zone"
    },
    {
      "State": "available",
      "OptInStatus": "opt-in-not-required",
      "Messages": [],
      "RegionName": "ap-northeast-1",
      "ZoneName": "ap-northeast-1c",
      "ZoneId": "apne1-az1",
      "GroupName": "ap-northeast-1",
      "NetworkBorderGroup": "ap-northeast-1",
      "ZoneType": "availability-zone"
    },
    {
      "State": "available",
      "OptInStatus": "opt-in-not-required",
      "Messages": [],
      "RegionName": "ap-northeast-1",
      "ZoneName": "ap-northeast-1d",
      "ZoneId": "apne1-az2",
      "GroupName": "ap-northeast-1",
      "NetworkBorderGroup": "ap-northeast-1",
      "ZoneType": "availability-zone"
    }
  ]
}

```

---

**?api=ec2:describe_availability_zones&region=ap-northeast-1&select=ZoneName:ZoneId**

```json
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

---

**?api=ec2:describe_instance_status&select=InstanceState.Name:InstanceId**

```json
{
  "InstanceStatuses": [
    {
      "InstanceState.Name": "running",
      "InstanceId": "i-xxxxxx"
    },
    {
      "InstanceState.Name": "running",
      "InstanceId": "i-xxxxxx"
    }
  ]
}
```

---

**?api=ec2:describe_instances&arg=%7b"Filters":[%7b"Name":"instance-type","Values":["t3.small"]%7d]%7d**

```json
{
  "Reservations":[
    {
      "Groups": [],
      "Instances": [
        {
          "AmiLaunchIndex": 0,
          "ImageId": "ami-xxxxxxxxxxxxxxxxx",
           　...snip...
        }
      ]
    }
  ]
}
```

---

**?api=ec2:describe_instances&flatten**

```json
{
  "Instances": [
    {
      "AmiLaunchIndex": 0,
      "ImageId": "ami-xxxxxxxxxxxxxxxxx",
      "InstanceId": "i-xxxxxxxxxxxxxxxxx",
        ...snip...
    }
  ]
}
```

---

**?api=ec2:describe_instances&flatten&select=InstanceId**

```json
{
  "Instances": [
    {"InstanceId": "i-xxxxxxxxxxxxxxxxx"},
    {"InstanceId": "i-xxxxxxxxxxxxxxxxx"},
    {"InstanceId": "i-xxxxxxxxxxxxxxxxx"},
     ...snip...
  ]
}
```

---

**?api=cloudwatch:get_metric_widget_image&arg=%7b%22MetricWidget%22:%22%7b%5c%22metrics%5c%22:[[%5c%22AWS/Config%5c%22,%5c%22ConfigurationItemsRecorded%5c%22,%5c%22ResourceType%5c%22,%5c%22AWS::EC2::VPC%5c%22]],%5c%22start%5c%22:%5c%22-PT3H%5c%22,%5c%22end%5c%22:%5c%22P0D%5c%22%7d%22%7d**

```json
{
  "MetricWidgetImage" : "iVBORw0KGgoAAAANSUh ...snip... "
}
```

---

**?api=ec2:describe_network_interfaces&select=NetworkInterfaceId:PrivateIpAddresses..PrivateIpAddress**

```json
{
  "NetworkInterfaces": [
    {
      "NetworkInterfaceId": "eni-xxxxxxxx",
      "PrivateIpAddresses..PrivateIpAddress": [
        "172.31.12.34"
      ]
    },
    {
      "NetworkInterfaceId": "eni-xxxxxxxx",
      "PrivateIpAddresses..PrivateIpAddress": [
        "172.31.56.78"
      ]
    }
  ]
}
```

---

**?api=s3:list_buckets&cache=1**

**?api=s3:list_buckets&cache=999999999**

**?api=s3:list_buckets&cache=never**

---
---

## ❌ NG Case

---

**(no paremeter)**

**?aaa**

**?api=hooo**

```json
{
  "Error_Message":"Invalid api parameter. example: api=ec2:describe_subnets"
}
```

---

**?api=ec2:describe_aabbcc**

```json
{
  "Error_Message":"'describe_aabbcc' probably incorrect"
}
```

---

**?api=s3:get_bucket_acl**

```json
{
  "Error_Message":"Parameter validation failed:\nMissing required parameter in input: \"Bucket\""
}
```

---

**?api=cloudwatch:describe_alarms&arg=%7b"aaa":"bbb"%7d**

```json
{
  "Error_Message":"Parameter validation failed:\nUnknown parameter in input: \"aaa\", must be one of: AlarmNames, AlarmNamePrefix, AlarmTypes, ChildrenOfAlarmName, ParentsOfAlarmName, StateValue, ActionPrefix, MaxRecords, NextToken"
}
```

---

**?api=ec2:describe_instances&arg=%7b"aaa:[]%7d**

```json
{
  "Error_Message":"Failed to decode parameter 'arg'"
}
```

---

**?api=ec2:describe_instances&arg={}**

```text
HTTP ERROR 400
```

(caution: ```{``` and ```}``` must be encoded)

---
