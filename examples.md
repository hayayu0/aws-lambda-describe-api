# aws-lambda-describe-api examples

## ✅ OK Case

---

**?api=ec2:describe_availability_zones&region=us-west-1**

```json
{"AvailabilityZones": [{"State": "available", "OptInStatus": "opt-in-not-required", "Messages": [], "RegionName": "us-west-1", "ZoneName": "us-west-1b", "ZoneId": "usw1-az3", "GroupName": "us-west-1", "NetworkBorderGroup": "us-west-1", "ZoneType": "availability-zone"}, {"State": "available", "OptInStatus": "opt-in-not-required", "Messages": [], "RegionName": "us-west-1", "ZoneName": "us-west-1c", "ZoneId": "usw1-az1", "GroupName": "us-west-1", "NetworkBorderGroup": "us-west-1", "ZoneType": "availability-zone"}]}
```

---

**?api=ec2:describe_availability_zones&indent=2**

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

**?api=ec2:describe_availability_zones&select=ZoneName**

```json
{"AvailabilityZones": [{"ZoneName": "ap-northeast-1a"}, {"ZoneName": "ap-northeast-1c"}, {"ZoneName": "ap-northeast-1d"}]}
```

---

**?api=ec2:describe_availability_zones&select=ZoneName:ZoneId**

```json
{"AvailabilityZones": [{"ZoneName": "ap-northeast-1a", "ZoneId": "apne1-az4"}, {"ZoneName": "ap-northeast-1c", "ZoneId": "apne1-az1"}, {"ZoneName": "ap-northeast-1d", "ZoneId": "apne1-az2"}]}
```

---

**?api=ec2:describe_instance_status&select=InstanceState.Name:InstanceId**

```json
{"InstanceStatuses": [{"InstanceState.Name": "running", "InstanceId": "i-xxxxxx"}, {"InstanceState.Name": "running", "InstanceId": "i-xxxxxx"}]}
```

---

**?api=ec2:describe_availability_zones&arg=%7b"ZoneNames":["ap-northeast-1c"]%7d**
<br>
 or
<br>
**?api=ec2:describe_availability_zones&arg=%7b%22ZoneNames%22:%5b%22ap-northeast-1c%22%5d%7d**

```json
{"AvailabilityZones": [{"State": "available", "OptInStatus": "opt-in-not-required", "Messages": [], "RegionName": "ap-northeast-1", "ZoneName": "ap-northeast-1c", "ZoneId": "apne1-az1", "GroupName": "ap-northeast-1", "NetworkBorderGroup": "ap-northeast-1", "ZoneType": "availability-zone"}]}
```

---

**?api=ec2:describe_instances&arg=%7b"Filters":[%7b"Name":"instance-type","Values":["t3.small"]%7d]%7d**

```json
{"Reservations": [{"Groups": [], "Instances": [{"AmiLaunchIndex": 0, "ImageId": "ami-xxxxxxxxxxxxxxxxx" 　...snip...　]}
```

---

**?api=ec2:describe_instances&flatten**

```json
{"Instances": [{"AmiLaunchIndex": 0, "ImageId": "ami-xxxxxxxxxxxxxxxxx", "InstanceId": "i-xxxxxxxxxxxxxxxxx",  ...snip...　]}
```

---

**?api=ec2:describe_instances&flatten&select=InstanceId**

```json
{"Instances": [{"InstanceId": "i-xxxxxxxxxxxxxxxxx"}, {"InstanceId": "i-xxxxxxxxxxxxxxxxx"}, {"InstanceId": "i-xxxxxxxxxxxxxxxxx"}, ...snip... ]}
```

---

**?api=cloudwatch:get_metric_widget_image&arg=%7b%22MetricWidget%22:%22%7b%5c%22metrics%5c%22:[[%5c%22AWS/Config%5c%22,%5c%22ConfigurationItemsRecorded%5c%22,%5c%22ResourceType%5c%22,%5c%22AWS::EC2::VPC%5c%22]],%5c%22start%5c%22:%5c%22-PT3H%5c%22,%5c%22end%5c%22:%5c%22P0D%5c%22%7d%22%7d**

```json
{ "MetricWidgetImage" : "iVBORw0KGgoAAAANSUh ...snip... " }
```

---

**?api=ec2:describe_availability_zones&cache=1**

**?api=ec2:describe_availability_zones&cache=999999999**

**?api=ec2:describe_availability_zones&cache=never**

<br>

---

## ❌ NG Case

---

**(no paremeter)** 

**?aaa** 

**?api=hooo**

```json
{"ERROR":"Bad Request"}
```

---

**?api=ec2:create_subnets**

```json
{"ERROR":"invalid api parameter.  OK example: api=ec2:describe_subnets"}
```

---

**?api=ec2:describe_aabbcc**

```json
{"ERROR":"'describe_aabbcc'"}
```

---

**?api=s3:get_bucket_acl**

```json
{"ERROR": "Parameter validation failed:\nMissing required parameter in input: \"Bucket\""}
```

---

**?api=cloudwatch:describe_alarms&arg=%7b"aaa":"bbb"%7d**

```json
{"ERROR": "Parameter validation failed:\nUnknown parameter in input: "aaa", must be one of: AlarmNames, AlarmNamePrefix, AlarmTypes, ChildrenOfAlarmName, ParentsOfAlarmName, StateValue, ActionPrefix, MaxRecords, NextToken"}
```

---

**?api=ec2:describe_instances&arg=%7b"aaa:[]%7d**

```json
{
    "Error Message": "parameter arg decode error"
}
```

---

**?api=ec2:describe_instances&arg={}**

(```{``` and ```}``` must be encoded)

```
HTTP ERROR 400
```

---
