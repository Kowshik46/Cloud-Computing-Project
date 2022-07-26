import json
import boto3
from datetime import datetime
from uuid import uuid4
def lambda_handler(event, context):
    s3=boto3.client('s3')
    bucket='auditstoragebucket'
    Resources=int(event['key1'])
    if Resources == 0:
        Resources =  'Lambda'
    else :
        Resources = 'Ec2'
    Parallel=int(event['key2'])
    minhistory=int(event['key3'])
    signal=int(event['key4'])
    if signal == 0 :
        signal ='buy'
    else :
        signal ='sell'
    shots=str(event['key5'])
    avg_95=float(event['key6'])
    avg_99=float(event['key7'])
    timeee=float(event['key8'])
    data= {"Resources":Resources,"Parallel":Parallel,"minhistory":minhistory,"signal":signal,"shots":shots,"avg_95":avg_95,"avg_99":avg_99,"timeee":timeee}
    uniqueid = str(datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4()))
    key="store" + str(uniqueid) + str(Resources) + str(uniqueid) + str(timeee)+str(avg_95)+ ".json"
    upload=bytes(json.dumps(data).encode('UTF-8'))
    s3.put_object(Bucket=bucket,Key=key,Body=upload)
    return "sucess"
   
