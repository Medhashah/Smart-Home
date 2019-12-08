import json
import boto3
from datetime import datetime
import random
import time
import random
from decimal import Decimal
from datetime import datetime  
from datetime import timedelta   
from boto3.dynamodb.conditions import Key, Attr

#That's the lambda handler, you can not modify this method
# the parameters from JSON body can be accessed like deviceId = event['deviceId']

def lambda_handler(event, context):
    # Instanciating connection objects with DynamoDB using boto3 dependency
    
    print(event)
    Name = event['message']['Name']
    PhoneNumber = event['message']['PhoneNumber']
    Photo_name = event['message']['Photo']
    
    # Getting the current datetime and transforming it to string in the format bellow
    # eventDateTime = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    # FaceId = event['FaceId']
    
    # Putting a try/catch to log to user when some error occurs
    
    client=boto3.client('rekognition')    
    response=client.index_faces(CollectionId='Collection_1',
                                Image={'S3Object':{'Bucket':'layers-opencv-hkm','Name':Photo_name}},
                                ExternalImageId=Photo_name,
                                MaxFaces=1,
                                QualityFilter="AUTO",
                                DetectionAttributes=['ALL'])
    
    print ('Results : ' ) 	
    print('Faces indexed:')						
    for faceRecord in response['FaceRecords']:
        face_id = faceRecord['Face']['FaceId']
        print('  Face ID: ' + face_id)
        print('  Location: {}'.format(faceRecord['Face']['BoundingBox']))
        current_timestamp = datetime.now()
        current_timestamp = Decimal(str(datetime.timestamp(current_timestamp)))
        #client = boto3.client('dynamodb')
        dynamodb = boto3.resource('dynamodb')
        TableVisitor = dynamodb.Table('Visitor')
        TableVisitor.put_item(
          Item={
                'FaceId': face_id,
                'Name': Name ,
                'phoneNumber':PhoneNumber,
                'photos': [
                        {
                        'objectKey': Photo_name,
                        'bucket': 'layers-opencv-hkm',
                        'createdTimestamp': current_timestamp
                        }
                    ]

            }
        )
        print("Entry entered into Visitor table")
        
        Otp_random = random.randrange(100000,999999)
        print(Otp_random)
        
        TablePassCodes = dynamodb.Table('passcodes')
        TablePassCodes.put_item(
              Item={
                    'guestid': face_id,
                    'otp':Otp_random,
                    'TimeStamp': current_timestamp
                }
            )
        print("Entry entered into passcode table")   
         
          # sns_client = boto3.client('sns')
        # sns_client.publish(
        #         PhoneNumber=PhoneNumber,
        #       Message="Hi, enter the otp:"+ Otp_random +" to the link below -> https://wtwo2.s3.amazonaws.com/wp2.html"
        #     )
            
        print("Hi, enter the otp:"+ str(Otp_random) +" to the link below -> https://wtwo2.s3.amazonaws.com/wp2.html")    
         
                
    response = 'OTP sent to the Visitor'
            
    return {
        'statusCode': 200,
        'body': response
        }
    
    