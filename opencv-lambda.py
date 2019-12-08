import json
import cv2
import boto3
import base64
import time
import random
from decimal import Decimal
from datetime import datetime  
from datetime import timedelta   
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
    
    #TODO implement
    print("getting the results from data stream")
    print(event)
    #event['Records'][0]['kinesis']['data']
    decoded_json = base64.decodestring(bytes(event['Records'][0]['kinesis']['data'],'utf-8'))
    
    #decoded_json = base64.decodestring(bytes(event['data'],'utf-8'))   
    decoded_json = json.loads(decoded_json)
    
    print("decoded_json fragment number")
    print(decoded_json['InputInformation']['KinesisVideo']['FragmentNumber'])
    
    if len(decoded_json['FaceSearchResponse'])>0 :
        kvs_client = boto3.client('kinesisvideo')
        kvs_data_pt = kvs_client.get_data_endpoint(
            StreamARN="arn:aws:kinesisvideo:us-east-1:313591084191:stream/assignment2/1572899165829", # kinesis stream arn
            APIName='GET_MEDIA'
        )
        print("printing kvs data point")
        print(kvs_data_pt)
        
        end_pt = kvs_data_pt['DataEndpoint']
        kvs_video_client = boto3.client('kinesis-video-media', endpoint_url=end_pt, region_name='us-east-1') # provide your region
        kvs_stream = kvs_video_client.get_media(
            StreamARN="arn:aws:kinesisvideo:us-east-1:313591084191:stream/assignment2/1572899165829", # kinesis stream arn
            StartSelector={'StartSelectorType': 'FRAGMENT_NUMBER',
                'AfterFragmentNumber': decoded_json['InputInformation']['KinesisVideo']['FragmentNumber']
            } # to keep getting latest available chunk on the stream
        )
        print("printing kvs stream")
        print(kvs_stream)
    
        # datafeed = kvs_stream['Payload'].read()
        # print("datafeed done..")
        # fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # print("videowriter four done..")
        # out = cv2.VideoWriter('/tmp/stream.avi',fourcc, 20.0, (640,480))
        # print("videowriter done..")
    
        with open('/tmp/stream.avi', 'wb') as f:
            print("inside loop")
            streamBody = kvs_stream['Payload'].read(1024*16384)
            print("got streamBody")
            f.write(streamBody)
            print("write streamBody done")
            # streamBody = kvs_stream['Payload'].read() # reads min(16MB of payload, payload size) - can tweak this
            # f.write(streamBody)
            # use openCV to get a frame
            cap = cv2.VideoCapture('/tmp/stream.avi')
            print("cap thing done")
            # use some logic to ensure the frame being read has the person, something like bounding box or median'th frame of the video etc
            ret, frame = cap.read() 
            t = str(time.time())
            print("time->",t)
            cv2.imwrite('/tmp/frame-'+t+'.jpg', frame)
            s3_client = boto3.client('s3')
            s3_client.upload_file(
                '/tmp/frame-'+t+'.jpg',
                'layers-opencv-hkm', # replace with your bucket name
                'frame-'+t+'.jpg',
                ExtraArgs={'ACL': 'public-read'}
            )
            cap.release()
            print('Image uploaded')
            client=boto3.client('rekognition')
            
            photo = 'frame-'+t+'.jpg'
            print("photoname",photo)
        if len(decoded_json['FaceSearchResponse'][0]['MatchedFaces']) == 0:
            # sns_client = boto3.client('sns')
            # sns_client.publish(
            #         PhoneNumber='3473833470',
            #       Message="Hi, Some unknown visitor is in front of the door. Visit the link if you want accept -> https://wpone.s3.amazonaws.com/wp1.html?photo="+photo
            #     )
                
            print("Hi, Some unknown visitor is in front of the door. Here is the link for the image -> https://layers-opencv-hkm.s3.amazonaws.com/"+photo+" . Visit the link if you want accept -> https://wpone.s3.amazonaws.com/wp1.html?photo="+photo)    
                
            #response=client.index_faces(CollectionId='Collection_1',
            #                             Image={'S3Object':{'Bucket':'layers-opencv-hkm','Name':photo}},
            #                             ExternalImageId=photo,
            #                             MaxFaces=1,
            #                             QualityFilter="AUTO",
            #                             DetectionAttributes=['ALL'])
        
            # print ('Results for ' + photo) 	
            # print('Faces indexed:')						
            # for faceRecord in response['FaceRecords']:
            #      print('  Face ID: ' + faceRecord['Face']['FaceId'])
            #      print('  Location: {}'.format(faceRecord['Face']['BoundingBox']))
             
        else:
            print("its a matched face")
            #Taking only 1st matched face
            Matched_faceId = decoded_json['FaceSearchResponse'][0]['MatchedFaces'][0]['Face']['FaceId']
            
            
            
            dynamodb = boto3.resource('dynamodb')
            client = boto3.client('dynamodb')
            
            
            
            TableVisitor = dynamodb.Table('Visitor')
            Matched_face_response = TableVisitor.query(KeyConditionExpression=Key('FaceId').eq(Matched_faceId))
            
            
            TablePassCodes = dynamodb.Table('passcodes')
            Matched_face_response_Passcode = TablePassCodes.query(KeyConditionExpression=Key('guestid').eq(Matched_faceId))
            print(Matched_face_response_Passcode)
            if len(Matched_face_response_Passcode['Items'])==0:
            
                TablePassCodes = dynamodb.Table('passcodes')
                Otp_random = random.randrange(100000,999999)
                print(Otp_random)
                current_timestamp = datetime.now()
                timestamp_expire  = current_timestamp + timedelta(minutes=5)
                timestamp_expire = datetime.timestamp(timestamp_expire) 
                timestamp = Decimal(str(timestamp_expire))
                current_timestamp = Decimal(str(datetime.timestamp(current_timestamp)))
                print(timestamp)
                
                TablePassCodes.put_item(
                  Item={
                        'guestid': Matched_faceId,
                        'otp':Otp_random,
                        'TimeStamp': timestamp
                    }
                )
                
                
                result = TableVisitor.update_item(
                        Key={
                            'FaceId': '5f52106b-9221-427e-a4f1-98f99887fe26'
                        },
                        UpdateExpression="SET photos = list_append(photos, :i)",
                        ExpressionAttributeValues={
                            ':i': [{
                            'objectKey': photo,
                            'bucket': 'layers-opencv-hkm',
                            'createdTimestamp': current_timestamp
                            }]
                        },
                        ReturnValues="UPDATED_NEW"
                    )
                print("updated the row")
                
                Matched_face_response = TableVisitor.query(KeyConditionExpression=Key('FaceId').eq(Matched_faceId))
                print("Matched_face_response",Matched_face_response)
                
                phone_number = Matched_face_response['Items'][0]['phoneNumber']
                print(phone_number)
                print("otp sent to above number:")
                print(Otp_random)
                # sns_client = boto3.client('sns')
                # sns_client.publish(
                #     PhoneNumber=phone_number,
                #   Message="Hi, enter the following OTP: "+ Otp_random +" Enter the  OTP in the link provided below: https://wtwo2.s3.amazonaws.com/wp2.html"
                # )
                
            else:
                print("Face already processed , so no more computing....")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!-----------')
    }
