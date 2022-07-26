import json
import boto3 
def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('auditstoragebucket')
    body=[]
    for obj in bucket.objects.all():
            key = obj.key
            body.append(obj.get()['Body'].read())
    return body
