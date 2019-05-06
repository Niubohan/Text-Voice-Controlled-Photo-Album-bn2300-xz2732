import json
import boto3
import time
from botocore.vendored import requests


es_domian = 'https://vpc-photos-vw2vqftvw3e6dqyojzr5m7x3l4.us-east-1.es.amazonaws.com/photos/_doc'
headers = {'Content-Type' : 'application/json'}

def lambda_handler(event, context):
    client=boto3.client('rekognition')
    print(client)
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key'] 
        print(key)
        label_res = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':key}},
            MaxLabels=100, MinConfidence=50)
        print('1')
        labels = [label['Name'] for label in label_res['Labels']]
        print(labels)
        fields = {
                'objectKey': key,
                'bucket': bucket,
                'createdTimestamp': time.time(),
                'labels': labels
        }
        response = requests.request('POST', es_domian, headers=headers, data=json.dumps(fields))
        print(response.json())   
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
