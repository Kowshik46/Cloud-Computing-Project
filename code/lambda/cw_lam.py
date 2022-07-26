import json
import random

def lambda_handler(event, context):
    #var95 =[]
    #var99 =[]
    mean =float(event['key1'])
    std = float(event['key2'])
    shots = int(event['key3'])

    simulated = [random.gauss(mean,std) for x in range(shots)]
    simulated.sort(reverse=True)
    var95_tem = simulated[int(len(simulated)*0.95)]
    var99_tem = simulated[int(len(simulated)*0.99)]
    return var95_tem,var99_tem
    

