import json
import boto3
import random
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    client = boto3.client('dynamodb')
    print(event)
    TablePassCodes = dynamodb.Table('passcodes')
    TableVisitors = dynamodb.Table('Visitor')
    flag=0
    Otp_entered = event['message']['OneTimePassword']
    resp = TablePassCodes.scan()
    for values in resp['Items']:
        if str(values['otp']) == Otp_entered:
            guestid = values['guestid']
            res = TableVisitors.scan()
            for v in res['Items']:
                if v['FaceId'] == guestid:
                    name = v['Name']
            flag =1
            response = 'Hello  '+ name + ', Validation Successfull'
            break
    
    if flag == 0:
        response = 'Incorrect OTP, Permission Denied'
        
    return {
        'statusCode': 200,        
        'body': response  }
    
  
  

    
    
    
    
    
    
    
    
    
    