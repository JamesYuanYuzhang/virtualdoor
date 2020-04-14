import json
import boto3
from datetime import datetime
from random import choice
from boto3.dynamodb.conditions import Key, Attr
import time
s3 = boto3.resource('s3')
bucketname="virtualdoor"



def insert_into_visitors(faceid,name,email):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    visitors = dynamodb.Table("visitors")
    photos_key={}
    photos_key["objectKey"] = faceid+"_0.jpg"
    photos_key["bucket"]="virtualdoor"
    photos_key["createdTimestamp"] = str(datetime.now())
    item = dict()
    item["faceId"] = faceid
    item["name"] = name
    item["email"] = email
    item["photos"] = [photos_key]
    # s3.Object(bucketname,photos_key["objectKey"]).copy_from(CopySource=bucketname+"/frame.jpg")
    # s3.Object(bucketname,'frame.jpg').delete()
    copy_source = {
    'Bucket': bucketname,
    'Key': "frame.jpg"
    }
    s3.meta.client.copy(copy_source, bucketname,photos_key["objectKey"] )
    res = visitors.put_item(Item=item)
    print(res)
    return True

def create_OTP(OTP_length=6):
    template=list(map(str,[i for i in range(10)]))
    return "".join(choice(template) for i in range(OTP_length))

def store_otp_in_passcodes(faceid,email):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    passcodes = dynamodb.Table("passcodes")
    while True:
        OTP = create_OTP()
        res = passcodes.scan(FilterExpression=Attr('OTP').eq(OTP))["Items"]
        print(res)
        if not res:
            break
    response = passcodes.put_item(Item={"faceId": faceid, "OTP": OTP, "ttl": str(300 + int(time.time()))})
    send_msg_to_visitor(email,OTP)

def send_msg_to_visitor1(email,OTP):
    email=str(email)
    if not email.startswith("+1"):
        email = "+1" + email
    sns = boto3.client("sns", region_name="us-east-1")
    msg="The pass code is {}".format(OTP)
    sns.publish(email=email, Message=str(msg))
    print("send out successfully!")

def send_msg_to_visitor(email,OTP):
    #email = "1661257855@qq.com"
    client = boto3.client('ses', region_name="us-east-1")
    response = client.send_email(
        # Source="virtualdoor@gmail.com",
        Source="yy2979@columbia.edu",
        Destination={'ToAddresses': [email], },
        Message={
            'Subject': {
                'Data': 'string',
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {'Charset': "UTF-8",
                         'Data': OTP,
                         }, }}
    )

def search_collection(client,collectionid="virtualDoor",bucketname="virtualdoor",name="frame.jpg"):
    response = client.search_faces_by_image(
        CollectionId=collectionid,
        Image={
            'S3Object': {
                'Bucket': bucketname,
                'Name': name
            }
        },
    )
    return response["FaceMatches"]

def lambda_handler(event, context):
    # TODO implement
    #输入格式改一下即可
    rek_client = boto3.client('rekognition')
    faceid=search_collection(rek_client)[0]["Face"]["FaceId"]
    print("(*********************")
    print(faceid)
    name,email=event["name"],event["email"]
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps(name+email+faceid)
    # }
    insert_into_visitors(faceid,name,email)
    store_otp_in_passcodes(faceid,email)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
