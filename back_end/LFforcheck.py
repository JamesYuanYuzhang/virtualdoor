import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import time

def check(OTP):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    passcodes = dynamodb.Table("passcodes")
    res = passcodes.scan(FilterExpression=Attr('OTP').eq(OTP))["Items"]
    print(res)
    if res:
        response=passcodes.delete_item(Key={"faceId":res[0]["faceId"]})
        print(response)
        visitors = dynamodb.Table("visitors")
        response=visitors.query(KeyConditionExpression=Key("faceId").eq(res[0]["faceId"]),
                                FilterExpression=Key("ttl").gt(int(time.time()))
                                )["Items"]
        print(response)
        return "Hello, {}".format(response[0]["name"])
    else:
        return "The pass code is wrong, please try again!"

def lambda_handler(event, context):
    # TODO implement
    msg=check(event["otp"])
    return {
        'statusCode': 200,
        'body': msg
    }
