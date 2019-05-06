import json
import botocore.session
import time
from botocore.vendored import requests
import boto3

userId = str(time.time())
es_domin = "https://vpc-photos-vw2vqftvw3e6dqyojzr5m7x3l4.us-east-1.es.amazonaws.com/photos/_search"

def lex_response(msg):
    session = botocore.session.get_session()
    client = session.create_client('lex-runtime')
    response = client.post_text(
        botName='Photosearch',
        botAlias='Photosearch',
        userId=userId,
        inputText= msg
        )
    print(response)
    try:
        labels = [label for label in response['slots'].values() if label]
        return labels
    except:
        return []

def es_search(labels):
    res = []
    for label in labels:
        url = es_domin + '?q=labels:{}&size=100'.format(label)
        #url = es_domin + '?q=bucket:bn2300-xz2732-photo'
        response = requests.request('GET', url).json()
        print(response)
        res += [item['_source']['objectKey'] for item in response['hits']['hits']]
    return list(set(res))

def transcribe_job():
    transcribe = boto3.client('transcribe')
    job_name = str(time.time())
    job_uri = "https://s3.amazonaws.com/bn2300-xz2732-photo/voice.wav"
    transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='wav',
        LanguageCode='en-US'
    )
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='hw3-task')
    msg = {
        'job': {
            'StringValue': job_name,
            'DataType': 'String'
        }
    }
    queue.send_message(MessageBody='message', MessageAttributes=msg)

def transcribe_search():
    sqs = boto3.resource('sqs')
    transcribe = boto3.client('transcribe')
    queue = sqs.get_queue_by_name(QueueName='hw3-task')
    message = queue.receive_messages(MessageAttributeNames=['job'])
    info = message[0].message_attributes
    job_name = info['job']['StringValue']
    status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    if status['TranscriptionJob']['TranscriptionJobStatus'] not in ['COMPLETED', 'FAILED']:
        return -1
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        res = requests.request('GET', uri).json()
        message[0].delete()
        return res["results"]["transcripts"][0]["transcript"]
    else:
        message[0].delete()
        return "1"

def lambda_handler(event, context):
    # TODO implement
    if 'params' not in event:
        transcribe_job()
        return {
        'statusCode': 200
        }
    if event['params']['querystring']['q'] == "?voiceserach":
        query = transcribe_search()
        if not query:
            return {
                'statusCode': 200,
                'body': {
                    'results' : "Pending"
                }
            }
    else:
        query = event['params']['querystring']['q']
    # query = "people"
    labels = lex_response(query)
    objects = es_search(labels)
    objects_url = ['https://s3.amazonaws.com/bn2300-xz2732-photo/' + object for object in objects]
    print(objects)
    return {
        'statusCode': 200,
        'body': {
            'results' : [{'url': object_url, 'labels': labels} for object_url in objects_url]
            }
    }
