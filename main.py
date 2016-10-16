import LeadPriceCalendar as DF
import sourceKeys as SK
import json
from datetime import datetime
from datetime import datetime  
from datetime import timedelta  
import apiai


#COMMUNICATE WITH API.AI
def parse(text,sessionId=0):
  # where x is text from user
  # sessionId is default 0 - get sessionId from response for subsequent parses
  ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
  request = ai.text_request()
  request.lang = 'en' 
  request.query = text
  request.session_id = sessionId
  response = json.load(request.getresponse())
  return response


#TAKES STRING DATE, RETURNS LIST OF CURRENT DATE+3 MORE DAYS
def timerange(time):
	lis = []
	lis.append(time)
	var = datetime.strptime(time,"%Y-%m-%d")
	for i in range (0,3):
		var = var + timedelta(days=i)
		lis.append(datetime.strftime(var,"%Y-%m-%d"))
	return lis


#RETURNS TOP 5 COUNTRIES MATCHED TO THE ARGUMENT LIST -- args is a list
def findLocation(args):
	dic1 = SK.giveKeywords()
	templis = dic1.keys()
	dic2 = dict((el,0) for el in templis)
	for i in dic2:
		for p in args:
			if str(p).title() in dic1[i]:
				dic2[i]+=1

	top5 = []
	for i in range (0,5):
		p = max(dic2.iterkeys(), key=(lambda key: dic2[key]))
		top5.append(p)
		print "TOP 5 MATCHES (UNICODE, LOCATION, HITS): "
		print dic1[p][1],
		print p,
		print dic2[p]
		dic2[p] = -1
	return top5


'''
test for matcher.
args = ['North America', 'Clean', 'City', 'Waterfall', 'Lake', 'Nature', 'Aurora', 'Hiking', 'Shopping']
print findLocation(args)
'''	



def returnFlights(goingFrom,price,goingWhen,goingWhere,duration):

	# js_raw = open('jsondata.json').read()
	# js_data = json.loads(js_raw)
	# stayingHowLong = str(js_data['result']['parameters']['duration']['duration']['amount'])
	# goingWhen = js_data['result']['parameters']['date']['date']
	# spendHowMuch = 10*js_data['result']['parameters']['price']['number']
	# goingFrom_temp = js_data['result']['context']['2']['parameters']['duration']['original.original']
	stayingHowLong = str(duration)
	goingWhen = goingWhen
	spendHowMuch = price
	goingFrom_temp = goingFrom


	#INTIALIZE TO 3CHAR AND 2CHAR UNICODE CHARACTERS
	goingWhere = SK.giveKeywords()[goingWhere][2]
	goingFrom = SK.giveKeywords()[goingFrom_temp][2]
	goingFromSales = SK.giveKeywords()[goingFrom_temp][1]


	#print js_data
	#op.latestdeparturedate(js_data['result']['parameters']['date']['date'])


	op = DF.LeadPriceCalendar()
	
	op.origin(goingFrom)
	op.lengthofstay(stayingHowLong)
	op.destination(goingWhere)
	op.departuredate(timerange(goingWhen))
	op.maxfare(spendHowMuch)
	op.pointofsalecountry(goingFromSales)

	
	#TESTING AND PRINTING
	for i in op.call()['FareInfo']:
		for p,q in i.items():
			print p,
			print ": " + str(q)
		print "\n"


 	js_raw = open('airlines.json').read()
 	js_data = json.loads(js_raw)
	res = ''
	#TESTING AND PRINTING
	res = res + "These are the flights I've found for you: \n"
	for i in op.call()['FareInfo']:
		for p in js_data['AirlineInfo']:
			#print i['LowestFare']['AirlineCodes'][0] + " ",
			#print p.keys()
			if i['LowestFare']['AirlineCodes'][0] in p.values():
				res = res+ p['AlternativeBusinessName']+"\n"
		res=res+ "Your round trip would  (Lowest Fares!) : " + str(i['LowestFare']['Fare']) + " " + i['CurrencyCode'] + "\n"
		res = res + "Across the dates: " + i['DepartureDateTime'] + " to " + i['ReturnDateTime'] + "\n\n" 

	return res

