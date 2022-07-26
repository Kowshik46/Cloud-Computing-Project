import os 
import logging 
from flask import Flask , request, render_template
import pandas as pd
import math
import random
import yfinance as yf
from datetime import date, timedelta,datetime
from pandas_datareader import data as pdr
import http.client
import statistics
import time 
from concurrent.futures import ThreadPoolExecutor
import os
os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred'
import boto3
# override yfinance with pandas – seems to be a common step
global flag1
flag1 = 0 
app = Flask(__name__) 
# various Flask explanations available at:  
# https://flask.palletsprojects.com/en/1.1.x/quickstart/ 
def doRender(tname, values={}):
	if not os.path.isfile( os.path.join(os.getcwd(), 
'templates/'+tname) ): #No such file
		return render_template('index.htm')
	return render_template(tname, **values) 

	
@app.route('/display', methods=['POST'])
def starter():
	if request.method == 'POST':
		
		l = request.form.get('Services')
		
		c = request.form.get('parallel')
		if l == '' or c == '':
			return doRender('index.htm',{'note': 'Please select all options'})
		else:		
				c = int(c)
				if l=='ec2':
					notes = 'EC2 Service Selected with '+str(c) +' resources please chaage any slection before starting the analysis'
				else :
					notes='Lambda Selected with '+str(c)+ ' resources please change any slection before starting the analysis'
				return doRender('services.htm',{'note': notes,'res':l,'par':c})
	
@app.route('/history', methods=['POST'])
def audit():
	rrrr = get_logs()
	audit_ttt = getaudit_tuple(rrrr)
	return doRender('history.htm',{'note':audit_ttt})
@app.route('/analysis', methods=['POST'])
def analysis(): 
	ana_start = time.time()
	global minhistory
	l = request.form.get('Services')
	c = int(request.form.get('parallel'))
	minhistory= int(request.form.get('days'))
	global shots 
	shots=int(request.form.get('shots'))
	signal = request.form.get('symbol')
	print(l)
	print(c)
	cc = c
	v95 =[]
	v99 =[]
	risk_95 =[]
	risk_99 = []
	global flag1
	ips_list_main=[]
	if l =="lam":
		datess = get_dates(signal,minhistory)
		final1,ttt =call_lam2(cc,signal,minhistory,shots)
		ttt=round(float(ttt),3)
		one,two = finalmanipulation(final1,cc)
		lennn =1
		lennn = len(one)
		if lennn == 0:
			lennn = 1
		avg95 = sum(one)/lennn
		avg99 = sum(two)/lennn
		avg95_list = [avg95]*lennn
		avg99_list = [avg99]*lennn
		rangess = range(len(datess))
		tupless = tuple(zip(datess,one,two))
		tupless2 = tuple(zip(datess,one,two,avg95_list,avg99_list))
		store_history(l,c,minhistory,signal,shots,avg95,avg99,ttt)
		#print (tupless2)
		letstrythis = "95 list is " + str(one)+"*******************************************************************************                     99 list is " + str(two)+ "avg og 95 risks = " + str(avg95)+"avg of 99 list is = "+str(avg99)+"Time taken for this is "+str(ttt)
	else :
		if flag1 == 1:
			terminate()
		if flag1 == 0:
			ips_list_main = call_ec2(c,minhistory,shots,signal)
			flag1 = 1
		if signal =='buy':
			sigg = 0
		else: 
			sigg = 1
		datess,one,two,ttt=ec2_run(c,minhistory,shots,sigg,ips_list_main)
		lennn =1
		lennn = len(one)
		if lennn == 0:
			lennn = 1
		avg95 = sum(one)/lennn
		avg99 = sum(two)/lennn
		datess = date_ec2(datess)
		avg95_list = [avg95]*lennn
		avg99_list = [avg99]*lennn
		tupless = tuple(zip(datess,one,two))
		tupless2 = tuple(zip(datess,one,two,avg95_list,avg99_list))  
		#return letstrythis
		store_history(l,c,minhistory,signal,shots,avg95,avg99,ttt)
	if len(datess) == 0 :
		waitt(datess) 
	rendered = time.time() - ana_start
	#print(rendered)
	return doRender('output.htm',{'data':tupless,'note':ttt,'data2':tupless2,'Avg95':avg95,'Avg99':avg99,'list95':one,'list99':two,'datesss':datess})

def date_ec2(datess1):
    tmplist= []
    for i in range(len(datess1)):
        tmp = datess1[i]
        tmp1 = tmp[6:]+','+tmp[3:5]+','+tmp[0:1]
        tmplist.append(tmp1)
    return (tmplist)
# catch all other page requests - doRender checks if a page is available (shows it) or not(index)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def mainPage(path):
	return doRender(path)
	
@app.route('/terminate', methods=['POST'])
def terminate():
	global flag1
	flag1 = 0
	ec2 = boto3.resource('ec2', 'us-east-1')
	print(ec2)
# iterate through instance IDs and terminate the
	ids= [instance.id for instance in ec2.instances.all()]
	print (ids)
	instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
	print(instances)
	for instance in instances:
		ec2.instances.filter(InstanceIds=ids).terminate()
	return doRender('staticc.htm')
@app.errorhandler(500) 
# A small bit of error handling 
def server_error(e): 
	logging.exception('ERROR!') 
	return """ An  error occurred: <pre>{}</pre> 
	""".format(e), 500 

def finalmanipulation(somethin,ccc):
    list95 = []
    list99 = []
    breker  = int(len(somethin)/ccc)
    temp = breker 
    temp1 = breker
    mutlipol = 2 
    for i in range(len(somethin)):
        if temp1 == 0 :
            temp1 = breker
            print("im herer")
            temp = breker*mutlipol
            mutlipol = mutlipol+1
        new  = str(somethin[i]).split()
        new_list = [s.replace("]", "") for s in new]
        new_list = [s.replace("[", "") for s in new_list]
        new_list = [s.replace(",", "") for s in new_list]
        if i < breker :
            list95.append(float(new_list[0]))
            list99.append(float(new_list[1]))
        else:
            new_95 = (list95[i-temp]+float(new_list[0])) / 2
            new_99 = (list99[i-temp]+float(new_list[1])) / 2
            list95[i-temp] = new_95
            list99[i-temp] = new_99          
            temp1 = temp1 -1 
    return list95,list99
#def call_lam(data,signal,minhistory,shots) :
#	global dateee 
#	dateee = []
#	mean = []
#	std= []
#	risk95=[]
#	risk99=[]
#	print (shots)
#	print(minhistory)
#	if signal == 'buy':
#		for i in range(minhistory, len(data)): 
#	    		if data.Buy[i]==1: # if we were only interested in Buy signals
#		        	meant=data.Close[i-minhistory:i].pct_change(1).mean()
#		        	stdt=data.Close[i-minhistory:i].pct_change(1).std()
#		        	temp_95,temp_99=exec_lamm (meant,stdt,shots)
#		        	dateee.append(data.index[i])
#		        	risk95.append(float(temp_95))
#		        	risk99.append(float(temp_99))
#		        	
#	else :
#		for i in range(minhistory, len(data)): 
#	    		if data.Sell[i]==1: # if we were only interested in Buy signals
#		        	meant=data.Close[i-minhistory:i].pct_change(1).mean()
#		        	stdt=data.Close[i-minhistory:i].pct_change(1).std()
#		        	temp_95,temp_99=exec_lamm (meant,stdt,shots)
#		        	dateee.append(data.index[i])
#		        	risk95.append(float(temp_95))
#		        	risk99.append(float(temp_99))
#	return risk95,risk99
	
#def exec_lamm(mean,std,shots):
#	host = "7h7zz2qst7.execute-api.us-east-1.amazonaws.com"
#	try:
#		h = http.client.HTTPSConnection(host)
#		json= '{ "key1": ' + str(mean) +',"key2": ' + str(std) +',"key3": '+ str(shots) +'}'
#		h.request("POST", "/default/function_one", json)
#		response = h.getresponse()
#		output = response.read().decode('utf-8')
#		rr95,rr99 = pretifylist2(output)
#	except IOError:
#		print( 'Failed to open', host)
#		      		
#	return rr95,rr99
#def pretifylist2(outputt): 
#    new1 = list(outputt.split())
#    new_list1 = [s.replace("]", "") for s in new1]
#    new_list1 = [s.replace("[", "") for s in new_list1]
#    new_list1 = [s.replace(",", "") for s in new_list1]
#    new_list1 = [s.replace("'", "") for s in new_list1]
#    return new_list1[0],new_list1[1]
def call_ec2(c,minhistory,shots,signal) :
	print("parallel resourses = ",c)
	print("minhistory ",minhistory)
	print("shots ",shots)
	print("signal",signal)
	print("thisi is fun:",minhistory+shots)
	dnsid = []
	dnsid = launch_ec2(c)
	print(dnsid)
	return  dnsid
def launch_ec2(c):
	listips =[]
	ec2 = boto3.resource('ec2', region_name='us-east-1')
	instances = ec2.create_instances(
	ImageId = 'ami-01e3ed106d2dd921d', 
	MinCount = 1,
	MaxCount = c,
	InstanceType = 't2.micro',
	KeyName = 'key1', # Make sure you have the named us-east-1kp
	SecurityGroups=['ssh'], # Make sure you have the named SSH
	BlockDeviceMappings = # extra disk
	[ {'DeviceName' : '/dev/sdf', 'Ebs' : { 'VolumeSize' : 10 } } ],
	#UserData=user_data # and user-data
	)
# Wait for AWS to report instance(s) ready.
	for i in instances:
		i.wait_until_running()
		# Reload the instance attributes
		i.load()
		ids= i.public_dns_name
		listips.append(ids)
		print("in launch ec2 dipksy ids :",listips)
	return listips
def ec2_run(c,minhistory,shots,signal,ip_list):
	datess =[]
	one=[]
	two=[]
	timeee=[]
	for i in range(c):
		print("in ec2_run")
		print(ip_list[i])
		host = ip_list[i]
		print (host)
		print("halting:",time.time())
		if i == 0:
			time.sleep(120) #just to make sure files are all setup and ready to go
		print("resumed",time.time())
		stringgg = "/ec2calc.py?"+str(shots)+"&"+str(signal)+"&"+str(minhistory)
		print(stringgg)
		try: 
			h = http.client.HTTPConnection(host)
			h.request("GET", stringgg)
			response = h.getresponse()
			output = response.read().decode('utf-8')
			#print(output)
			datess,one,two,timeee = ec2_stichstring(output,datess,one,two,timeee,i)
		except IOError:
			print( 'Failed to open', host)
	
	return datess,one,two,timeee
def ec2_stichstring(ott,datess,one,two,timeee,i):
		ott = ott.split("&")
		dates = ott[1]
		list_95=ott[2]
		list_99 = ott[3]
		timee = ott[4]
		dates=pretifylist2(dates)
		list_95=pretifylist2(list_95)
		list_99=pretifylist2(list_99)
		list_95 = [float(list_95[i]) for i in range(len(list_95))]
		list_99 = [float(list_99[i]) for i in range(len(list_99))]
		timee=timee[:15]
		timee=round(float(timee),3)
		print(timee)
		if i > 0: 
			list_95,list_99,timee = combineoutput(one,two,timeee,list_95,list_99,timee)
		return dates,list_95,list_99,timee
def pretifylist2(outputt):
	outputt=outputt.split()
	new_list1 = [s.replace("]", "") for s in outputt]
	new_list1 = [s.replace("[", "") for s in new_list1]
	new_list1 = [s.replace(",", "") for s in new_list1]
	new_list1 = [s.replace("'", "") for s in new_list1]
	new_list1 = [s.replace('"', '') for s in new_list1]
	new_list1 = [s.replace(" ", "") for s in new_list1]
	return new_list1
def combineoutput(one,two,timeee,list_952,list_992,timee2):
	combine95 = [statistics.mean(k) for k in zip(one,list_952)]
	combine99 = [statistics.mean(k) for k in zip(two,list_992)]
	tottime = timeee + timee2
	tottime=round(float(tottime),3)
	return combine95,combine99,tottime
	
def call_lam2(c,signal,minhistory,shots) :
    print("lam2")
    parallel = c
    print(c)
    dateees = []
    mean = []
    std= []
    timetaken = 0 
    start = time.time()
    print(shots)
    print(minhistory)
    runs=[value for value in range(c)]
    global oottt
    oottt=[]
    def getpage(id):
        try:
            print("intry")
            mean,std=getmean(signal,minhistory)
            print(len(mean))
            host = "7h7zz2qst7.execute-api.us-east-1.amazonaws.com"
            h = http.client.HTTPSConnection(host)
            for iiii in range(len(mean)):
                json= '{ "key1": ' + str(mean[iiii]) +',"key2": ' + str(std[iiii]) +',"key3": '+ str(shots) +'}'
                resptime = time.time()
                h.request("POST", "/default/function_one", json)
                #print("response time is :",time.time()-resptime)
                response = h.getresponse()
                dfff = response.read().decode('utf-8')
                oottt.append(dfff)
        except IOError:
                print( 'Failed to open ', host ) # Is the Lambda address correct?
        return "page "+str(id)
    def getpages():
        with ThreadPoolExecutor() as executor:
            results=executor.map(getpage, runs)
        return results
    #if __name__ == '__main__':
    #print(__name__)
    start = time.time()
    results = getpages()
    timetaken = time.time() - start
    print(timetaken)
    timetaken = time.time() - start
    return oottt,timetaken
def get_dates(signal,minhistory):
	print("in get_values")
	data = getdata()
	dateee = []
	if signal == 'buy':
		for i in range(minhistory, len(data)):
			if data.Buy[i]==1: # if we were only interested in Buy signals
				#meant=data.Close[i-minhistory:i].pct_change(1).mean()
				#stdt=data.Close[i-minhistory:i].pct_change(1).std()
				#mean.append(meant)
				#std.append(stdt)
				tmp = pd.to_datetime(data.index[i]).date()
				tmp = tmp.strftime("%Y,%m,%d")
				dateee.append(tmp)
	else:
		for i in range(minhistory, len(data)):
			if data.Sell[i]==1: # if we were only interested in Buy signals
				#meant=data.Close[i-minhistory:i].pct_change(1).mean()
				#stdt=data.Close[i-minhistory:i].pct_change(1).std()
				#mean.append(meant)
				#std.append(stdt)
				tmp = pd.to_datetime(data.index[i]).date()
				tmp = tmp.strftime("%Y,%m,%d")
				dateee.append(tmp)
				((pd.to_datetime(data.index[i]).date()).strftime("%d/%m/%Y"))
					#print("m,ean,std sent")
	return dateee

	

def pretifylist(outputt):
	new = new = list(outputt.split())
	new_list = [s.replace("]", "") for s in new]
	new_list = [s.replace("[", "") for s in new_list]
	new_list = [s.replace(",", "") for s in new_list]
	middle =int(len(new_list)/2)
	vv95 = new_list[0:middle]
	vv99 = new_list[middle:]
	return vv95,vv99
def getmean(signal,minhistory):
    print("inget")
    meaan=[]
    sttd=[]
    data = getdata()
    if signal == 'buy':
        for i in range(minhistory, len(data)): 
                if data.Buy[i]==1: # if we were only interested in Buy signals
                    meant=data.Close[i-minhistory:i].pct_change(1).mean()
                    stdt=data.Close[i-minhistory:i].pct_change(1).std()
                    meaan.append(meant)
                    sttd.append(stdt)
    else :
        for i in range(minhistory, len(data)): 
             if data.Sell[i]==1: # if we were only interested in Buy signals
                    meant=data.Close[i-minhistory:i].pct_change(1).mean()
                    stdt=data.Close[i-minhistory:i].pct_change(1).std()
                    meaan.append(meant)
                    sttd.append(stdt)
    return meaan,sttd
def get_logs():
    host = "g6uoe58308.execute-api.us-east-1.amazonaws.com"
    h = http.client.HTTPSConnection(host)
    h.request("POST", "/default/getdata")
    response = h.getresponse()
    dfff = response.read().decode('utf-8')
    return (dfff)
def getaudit_tuple(rrrr):
    temp = rrrr.split(",")
    new_list1 = [s.replace("{", "") for s in temp]
    new_list1 = [s.replace("}", "") for s in new_list1]
    new_list1 = [s.replace('"', '') for s in new_list1]
    new_list1 = [s.replace("[", "") for s in new_list1]
    new_list1 = [s.replace(']', '') for s in new_list1]
    new_list1 = [s.replace('\\', '') for s in new_list1]
    new_list1 = [s.replace(' ', '') for s in new_list1]
    res_list = []
    pa_list =[]
    min_lis=[]
    signal_list =[]
    shots_list=[]
    avg5_list =[]
    avg9_list =[]
    time_list =[]
    for i in range(len(new_list1)):
        tempppp = new_list1[i]
        if tempppp[0:2] == 'Re':
            paraaa = tempppp[10:]
            res_list.append(paraaa)
        elif tempppp[0:2] == 'Pa':
            paraaa = tempppp[9:]
            pa_list.append(paraaa)
        elif tempppp[0:2] == 'mi':
            paraaa = tempppp[11:]
            min_lis.append(paraaa)
        elif tempppp[0:2] == 'si':
            paraaa = tempppp[7:]
            signal_list.append(paraaa)
        elif tempppp[0:2] == 'sh':
            paraaa = tempppp[6:]
            shots_list.append(paraaa)
        elif tempppp[0:2] == 'ti':
            paraaa = tempppp[7:]
            time_list.append(paraaa)
        elif tempppp[0:6] == 'avg_95':
            paraaa = tempppp[7:]
            avg5_list.append(paraaa)
        elif tempppp[0:6] == 'avg_99':
            paraaa = tempppp[7:]
            avg9_list.append(paraaa)
    audit_tuple = tuple(zip(res_list,pa_list,min_lis,signal_list,shots_list,avg5_list,avg9_list,time_list)) 
    return audit_tuple
def store_history(res,par,minhistory,signal,shots,avg_95,avg_99,time):
    print("in store")
    if res == 'lam':
    	key1 = 0
    else :
    	key1 = 1
    key2 = str(par)
    key3 = str(minhistory)
    if signal == 'buy':
    	key4 = 0
    else :
    	key4 = 1
    key5 = str(shots)
    key6 = str(avg_95)
    key7 = str(avg_99)
    key8 = str(time)
    if avg_95 != 0:
	    host = "ixyhafen2d.execute-api.us-east-1.amazonaws.com"
	    h = http.client.HTTPSConnection(host)
	    json= '{ "key1": ' + str(key1) +',"key2": ' + str(key2) +',"key3": '+ str(key3) +',"key4": '+ str(key4) +',"key5": '+ str(key5) +',"key6": '+ str(key6) +',"key7": '+ str(key7) +',"key8": '+ str(key8) +'}'
	    h.request("POST", "/default/bucke_handling", json)
	    response = h.getresponse()
	    dfff = response.read().decode('utf-8')
	    print(dfff)
    else:
            print("it didnt worked") 	
def getdata():
	yf.pdr_override()
	data = today = date.today()
	decadeAgo = today - timedelta(days=3652)
	data = pdr.get_data_yahoo('BP.L', start=decadeAgo, end=today)
	data['Buy']=0
	data['Sell']=0
	for i in range(len(data)):
			realbody=math.fabs(data.Open[i]-data.Close[i])
			bodyprojection=0.3*math.fabs(data.Close[i]-data.Open[i])
		    # Hammr
			if data.High[i] >= data.Close[i] and data.High[i]-bodyprojection <= data.Close[i] and data.Close[i] > data.Open[i] and data.Open[i] > data.Low[i] and data.Open[i]-data.Low[i] > realbody:
				data.at[data.index[i], 'Buy'] = 1
				#print("BUY","H",data.index[i], data.Open[i], data.High[i], data.Low[i], data.Close[i])   
		    # Inverted Hammer
			if data.High[i] > data.Close[i] and data.High[i]-data.Close[i] > realbody and data.Close[i] > data.Open[i] and data.Open[i] >= data.Low[i] and data.Open[i] <= data.Low[i]+bodyprojection:
				data.at[data.index[i], 'Buy'] = 1
				#print("BUY","I",data.index[i], data.Open[i], data.High[i], data.Low[i], data.Close[i])
		    # Hanging Man
			if data.High[i] >= data.Open[i] and data.High[i]-bodyprojection <= data.Open[i] and data.Open[i] > data.Close[i] and data.Close[i] > data.Low[i] and data.Close[i]-data.Low[i] > realbody:
				data.at[data.index[i], 'Sell'] = 1
				#print("SELL,"M",data.index[i], data.Open[i], data.High[i], data.Low[i], data.Close[i])
		    # Shooting Star
			if data.High[i] > data.Open[i] and data.High[i]-data.Open[i] > realbody and data.Open[i] > data.Close[i] and data.Close[i] >= data.Low[i] and data.Close[i] <= data.Low[i]+bodyprojection:
				data.at[data.index[i], 'Sell'] = 1
	return data    
if __name__ == '__main__': 
	# Entry point for running on the local machine 
	# On GAE, endpoints (e.g. /) would be called. 
	# Called as: gunicorn -b :$PORT index:app, 
	# host is localhost; port is 8080; this file is index (.py) 
	app.run(host='127.0.0.1', port=8080, debug=True)







