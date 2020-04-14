import json
import boto3
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
from random import choice
import time

import sys

sys.path.insert(1, '/opt')
import cv2


def process_frame():
    rek_client = boto3.client('rekognition')
    KINESIS_STREAM_ARN = "arn:aws:kinesisvideo:us-west-2:226949131441:stream/KVS1/1584656440124"
    # KINESIS_STREAM_ARN = "arn:aws:kinesis:us-west-2:226949131441:stream/RekognitionVideoBlog-Stream"
    KINESIS_DATA_STREAM_ARN = "arn:aws:kinesis:us-west-2:226949131441:stream/kds1"
    BUCKET_NAME = "virtualdoor"
    # create_steam_processor(rek_client,KINESIS_STREAM_ARN,KINESIS_DATA_STREAM_ARN)

    # cap = cv2.VideoCapture('/tmp/stream.mkv')
    kvs_client = boto3.client('kinesisvideo')
    kvs_data_pt = kvs_client.get_data_endpoint(
        StreamARN=KINESIS_STREAM_ARN,  # kinesis stream arn
        APIName='GET_MEDIA',
        # StreamName="KVS1"
    )
    print("****************")
    print(kvs_data_pt)

    end_pt = kvs_data_pt['DataEndpoint']
    kvs_video_client = boto3.client('kinesis-video-media', endpoint_url=end_pt,
                                    region_name='us-west-2')  # provide your region
    kvs_stream = kvs_video_client.get_media(
        StreamARN=KINESIS_STREAM_ARN,  # kinesis stream arn
        StartSelector={'StartSelectorType': 'NOW'}  # to keep getting latest available chunk on the stream
    )
    print(kvs_stream)

    with open('/tmp/stream.mkv', 'wb') as f:
        # streamBody = kvs_stream['Payload'].read(1024*16384) # reads min(16MB of payload, payload size) - can tweak this
        streamBody = kvs_stream['Payload'].read(1024 * 1024)
        f.write(streamBody)
        # use openCV to get a frame
        cap = cv2.VideoCapture('/tmp/stream.mkv')
        # use some logic to ensure the frame being read has the person, something like bounding box or median'th frame of the video etc
        ret, frame = cap.read()
        print(frame)
        cv2.imwrite('/tmp/frame.jpg', frame)
        s3_client = boto3.client('s3')
        s3_client.upload_file(
            '/tmp/frame.jpg',
            BUCKET_NAME,  # replace with your bucket name
            'frame.jpg'
        )
        try:
            res = search_collection(rek_client)
            if res:
                # print(res)
                faceid = res[0]["Face"]["FaceId"]
                print(faceid)
                print("known face")
            else:
                response = rek_client.index_faces(
                    CollectionId="virtualDoor",
                    Image={
                        'S3Object': {
                            'Bucket': BUCKET_NAME,
                            'Name': 'frame.jpg'
                            # 'Version': 'string'
                        }
                    },
                    DetectionAttributes=[
                        'DEFAULT',
                    ],
                    MaxFaces=1,
                    QualityFilter='AUTO'
                )
                print(response)
                faceid = response["FaceRecords"][0]["Face"]["FaceId"]
                print("new face")
                # 这里的new是对于collection来说的
            photo_record = dict()
            photo_record["objectKey"] = faceid
            photo_record["bucket"] = BUCKET_NAME
            photo_record["createdTimestamp"] = str(datetime.now())
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            visitors = dynamodb.Table("visitors")
            passcodes = dynamodb.Table("passcodes")
            insert_into_visitors(s3_client, BUCKET_NAME, visitors, passcodes, photo_record, faceid)

            # name and email need to add

        except Exception as e:
            print(e)
        cap.release()
        # print('Image uploaded')


def lambda_handler(event, context):
    # from os import listdir
    # import json
    # print(listdir("/tmp"))
    process_frame()
    return {
        'statusCode': 200,
        'body': json.dumps("hello, lambda")
    }


def insert_into_visitors(s3, bucketname, visitors, passcodes, photos_key, faceId):
    res = search_dynamodb(visitors, faceId)
    # 先看在不在visitors里 如果在给他个最新的OTP
    print(faceId, res)
    if res:
        res = res[0]
        name,email=res["name"],res["email"]
        photo = res["photos"]
        photos_key["objectKey"] = photos_key["objectKey"] + "_" + str(len(photo)) + ".jpg"
        photo.append(photos_key)
        response = visitors.update_item(
            Key={"faceId": faceId},
            UpdateExpression="set photos = :updated",
            ExpressionAttributeValues={":updated": photo}
        )
        print(response)
        print("find an old face and update")
        s3.upload_file(
            '/tmp/frame.jpg',
            bucketname,  # replace with your bucket name
            photos_key["objectKey"]
        )
        if not passcodes.query(KeyConditionExpression=Key("faceId").eq(faceId),
                               FilterExpression=Key("ttl").gt(int(time.time())))["Items"]:
            while True:
                OTP = create_OTP()
                res = passcodes.scan(FilterExpression=Attr('OTP').eq(OTP))["Items"]
                print(res)
                if not res:
                    break
            # 还得判断一下是不是重复的OTP
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            verified = dynamodb.Table("verified")
            response = passcodes.put_item(Item={"faceId": faceId, "OTP": OTP, "ttl": 300 + int(time.time())})
            print(response)
            send_msg_to_visitor(email, OTP)
    else:
        # 如果这个人不在visitor里 那么先判断这个人是不是最近发过请求
        # 创建一个dynamobd叫verified存最近请求过没
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        verified = dynamodb.Table("verified")
        if verified.query(KeyConditionExpression=Key("faceId").eq(faceId),
                               FilterExpression=Key("timestamp").gt(int(time.time())))["Items"]:
            print("The unknown visitor has ask for OTP within last 5 minutes.")
            return
        else:
            response = verified.put_item(Item={"faceId": faceId, "timestamp": 300 + int(time.time())})
            send_msg_to_owner()
        # return
        # 后面的代码本地测试的时候用
    #     photos_key["objectKey"]+="_0.jpg"
    #     item=dict()
    #     item["faceId"]=faceId
    #     item["name"]=name
    #     item["email"]=email
    #     item["photos"]=[photos_key]
    #     res=visitors.put_item(Item=item)
    #     print(res)
    #     print("find a new face and insert success")
    # s3.upload_file(
    #     '/tmp/frame.jpg',
    #     bucketname,  # replace with your bucket name
    #     photos_key["objectKey"]
    # )
    # print(photos_key)
    # return


def create_OTP(OTP_length=6):
    template = list(map(str, [i for i in range(10)]))
    return "".join(choice(template) for i in range(OTP_length))





def send_msg_to_owner():
    email = "1661257855@qq.com"
    client = boto3.client('ses', region_name="us-east-1")
    link_url = "https://virtualdoor.s3-us-west-2.amazonaws.com/webpage1.html"
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
                         'Data': link_url,
                         }, }}
    )
    print(response)
    print("send request to owner")





def send_msg_to_visitor(email, OTP):
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
    print(response)
    print("send out successfully!")
    return


def search_collection(client, collectionid="virtualDoor", bucketname="virtualdoor", name="frame.jpg"):
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


def search_dynamodb(table, faceid):
    res = table.query(KeyConditionExpression=Key("faceId").eq(faceid))
    # print(res)
    return res["Items"]


def create_steam_processor(client, kvs, kds):
    # client = boto3.client('rekognition')
    response = client.create_collection(
        CollectionId="virtualDoor"
    )
    response = client.create_stream_processor(
        Input={
            'KinesisVideoStream': {
                'Arn': kvs
            }
        },
        Output={
            'KinesisDataStream': {
                'Arn': kds
            }
        },
        Name="virtualDoorStreamProcessor",
        Settings={
            'FaceSearch': {
                'CollectionId': "virtualDoor",
                'FaceMatchThreshold': 85.5
            }
        },
        RoleArn="arn:aws:iam::226949131441:role/Rekognition"
    )
    response = client.start_stream_processor(
        Name="virtualDoorStreamProcessor"
    )
    print(response)


def delete_processor(client, collectionid="virtualDoor", streamprocessor="virtualDoorStreamProcessor"):
    response = client.delete_collection(
        CollectionId=collectionid
    )
    print(response)
    response = client.delete_stream_processor(
        Name=streamprocessor
    )
    return response

# if __name__=="__main__":
#    process_frame()
# client = boto3.client('rekognition')
# res=delete_processor(client)
# print(res)
# res=create_steam_processor(client,"arn:aws:kinesisvideo:us-west-2:226949131441:stream/KVS1/1584656440124","arn:aws:kinesis:us-west-2:226949131441:stream/KDS1")
# print(res)
# response = client.search_faces(CollectionId="virtualDoor",FaceId="fd52061f-0995-4234-9744-79e392730f82")
# print(len(response["FaceMatches"]))
# dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
# table = dynamodb.Table("visitors")
# print(search_dynamodb(table,"94cfab8b-21b4-4896-8646-cae8229b20a1"))
# print(insert_into_dynamodb(table,"11.jpg","94cfab8b-21b4-4896-8646-cae8229b20a1"))
# table.put_item(Item={"faceId":"94cfab8b-21b4-4896-8646-cae8229b20a1"})
# print(search_dynamodb(table,"94cfab8b-21b4-4896-8646-cae8229b20a1"))


