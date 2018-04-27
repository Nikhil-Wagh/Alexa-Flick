# ********************************************************* #
# getMoviesNowShowing                                       #
#   - language                                              #
#   - city                                                  #
#                                                           #
# // getMoviesComingSoon                                    #
# //    - language                                          #
# //    - city                                              #
#                                                           #
# GetMovieDetails                                           #
#   - Movie name                                            #
#   - city                                                  #
#   - theatre                                               #
#                                                           #
# areSeatsAvailable                                         #
#   - movie name                                            #
#   - ShowTime                                              #
#   - city                                                  #
#                                                           #
# getTheatreList                                            #
#   - city                                                  #
#                                                           #
# ********************************************************* #

# To test it try this on your terminal
# python-lambda-local -f lambda_handler -t 10 lambda_function.py ./events/event.json



import re
import urllib2
import random
from datetime import datetime
from difflib import SequenceMatcher

class BookMyShowClient(object):
	NOW_SHOWING_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"Filter Impression:category\\\/now showing"},"products":\[{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}\]}}}'
	COMING_SOON_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"category\\\/coming soon"},"products":{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}}}}'
	DETAILED_REGEX = '{"VenueCode":"(.*?)","EventCode":"(.*?)","SessionId":(.*?),"ShowTime":"(.*?)","ShowTimeCode":"(.*?)","MinPrice":"(.*?)","MaxPrice":"(.*?)","Availability":"(.*?)","CutOffFlag":"(.*?)","ShowDateTime":"(.*?)","CutOffDateTime":"(.*?)","BestBuy":"(.*?)","ShowDateCode":"(.*?)","IsAtmosEnabled":"(.*?)","SessionUnpaidFlag":"(.*?)","SessionUnpaidQuota":"(.*?)","BestAvailableSeats":(.*?),"Attributes":"(.*?)","SessionCodFlag":"(.*?)","SessionCodQuota":"(.*?)","SessionCopFlag":"(.*?)","SessionCopQuota":"(.*?)","SessionPopUpDesc":"(.*?)","Class":"(.*?)"}'
	VENUE_REGEX = '{"VenueCode":"(.*?)","VenueName":"(.*?)","VenueAdd":"(.*?)","VenueLegends":"(.*?)","VenueOffers":"(.*?)","SessCount":"(.*?)","AllowSales":"(.*?)","CompCode":"(.*?)","Lat":"(.*?)","Lng":"(.*?)","SubRegCode":"(.*?)","SubRegName":"(.*?)","SubRegSeq":"(.*?)","VenueApp":"(.*?)","IsNewCinema":"(.*?)","IsFoodSales":"(.*?)","IsMultiplex":"(.*?)","IsFullSeatLayout":"(.*?)","Message":"(.*?)","MessageType":"(.*?)","MessageTitle":"(.*?)","CinemaUnpaidFlag":"(.*?)","MTicket":"(.*?)","PopUpDescription":"(.*?)","IsFullLayout":"(.*?)","CinemaCodFlag":"(.*?)","CinemaCopFlag":"(.*?)","TicketCancellation":"(.*?)","VenueInfoMessage":"(.*?)"}'

	def __init__(self, location = 'Bengaluru'):
		self.__location = location.lower()
		self.__url = "https://in.bookmyshow.com/%s/movies" % self.__location
		self.__html = None

	def set_url(self, url):
		self.__url = url
		self.__html = None

	def __download(self):
		req = urllib2.Request(self.__url, headers={'User-Agent' : "Magic Browser"})
		html = urllib2.urlopen(req).read()
		return html

	def get_now_showing(self):
		if not self.__html:
			self.__html = self.__download()
		now_showing = re.findall(self.NOW_SHOWING_REGEX, self.__html)
		return now_showing

	def get_coming_soon(self):
		if not self.__html:
			self.__html = self.__download()
		coming_soon = re.findall(self.COMING_SOON_REGEX, self.__html)
		return coming_soon

	def get_details(self):
		if not self.__html:
			self.__html = self.__download()

		venue = re.findall(self.VENUE_REGEX, self.__html)
		venue_list = dict()
		for row in venue:
			venue_list[row[0]] = row[1]

		details = re.findall(self.DETAILED_REGEX, self.__html)
		show_list = []
		for row in details:
			current = {}
			current['theatre_name'] = venue_list[row[0]]    # add theatre name
			current['show_time'] = row[3]                   # add time
			current['time_code'] = row[4]                   # add time code for eg '1700'
			current['min_price'] = row[5]
			current['max_price'] = row[6]
			current['class'] = row[-1]                      # Morning, afternoon
			show_list.append(current)
		return show_list



def lambda_handler(event, context):
	if event['request']['type'] == "LaunchRequest":
		return on_launch(event, context)
	elif event['request']['type'] == 'IntentRequest':
		return on_intent(event['request'])
	elif event['request']['type'] == 'SessionEndedRequest':
		return on_session_ended()
		

def on_launch(event, context):
	welcomeMessage = getWelcomeMessage()
	return response_plain_text(welcomeMessage, False, {}, "Welcome", welcomeMessage, "How can I help you?")


def on_intent(request):
	intent = request['intent']
	intent_name = request['intent']['name']

	if 'dialogState' in request:
		if request['dialogState'] == "STARTED" or request['dialogState'] == "IN_PROGRESS":
			return dialog_response(request['dialogState'], False)

	if intent_name == 'GetMoviesNowShowing':
		return GetMoviesNowShowing(intent)
	elif intent_name == 'GetMovieDetails':
		return GetMovieDetails(intent)
	elif intent_name == "AMAZON.HelpIntent":
		return do_help()
	elif intent_name == "AMAZON.StopIntent":
		return do_stop(attributes)
	elif intent_name == "AMAZON.CancelIntent":
		return do_stop()
	else:
		print ("Invalid Intent reply with help")
		do_help()

#This is working fine
def GetMoviesNowShowing(intent):
	city = getSlotValue(intent, 'CITY').lower()
	language = getSlotValue(intent, 'LANGUAGE').lower()	

	print(city, language)
	result = []
	
	bms_client = BookMyShowClient(city)
	try:
		now_showing = bms_client.get_now_showing()
	except Exception as e: # Error
		print(e.args)
		print(type(e))
		return response_plain_text(
				"Something went wrong, I'm terribly sorry",
				True,
				{},
				"Error",
				"I could not process your request at the moment.",
				"Please try again. I would love to hear from you again"
			)
	# No Error

	# ('Avengers: Infinity War', 'ET00073462', 'MT', '2D', '1', 'English')
	for movie in now_showing:
		if movie[5].lower() == language:
			result.append([movie[0], movie[3]])

	if len(result) > 0:
		outputSpeech, cardContent = getOSandCC(result)		
		return response_plain_text(
				"These are the movie" + ("s" if len(result) > 1 else "") + " which are screening in " + city + " right now. " + outputSpeech,
				True,
				{},
				"Movies in " + city,
				cardContent 
			)
		pass
	else:
		return response_plain_text(
				"Bummer I couldn't find anything for that language. There may be movies showing in other languages, please try that.",
				True,
				{},
				"Nothing to show",
				"No movies showing right now.\nTry changing the language you want to watch your movie in."
			)





	# if movieName != -1:
	# 	show_details = GetMovieDetails(bms_client, result, movieName, location)
	# 	listTheatres = []
	# 	for k in show_details.iterkeys():
	# 		listTheatres.append(k)

	# 	print(listTheatres)
	# 	print(show_details)

	# else:
	# 	hello
	# 	outputSpeech = "These are the movies which are showing in your area " 
	# 	for r in result:
	# 		outputSpeech += r[0] + " which is showed in dimension " + r[3] + " and the language is " + r[5]

	# 	return response_plain_text(outputSpeech, False, {}, str(len(result)) + " movies showing", result)


#url = https://in.bookmyshow.com/buytickets/bharat-ane-nenu-pune/movie-pune-ET00059033-MT/20180421
def GetMovieDetails(intent):
	city = getSlotValue(intent, 'CITY').lower()
	movie_name = getSlotValue(intent, 'NAME').lower()
	movie_name = movie_name.encode('ascii', 'ignore')


	movies_list = []
	
	bms_client = BookMyShowClient(city)
	try:
		now_showing = bms_client.get_now_showing()
	except Exception as e: # Error
		print(e.args)
		print(type(e))
		return response_plain_text(
				"Something went wrong, I'm terribly sorry",
				True,
				{},
				"Error",
				"I could not process your request at the moment.",
				"Please try again. I would love to hear from you again"
			)

	for movie in now_showing:
		if similar(movie[0], movie_name) : 
			movies_list.append(movie)

	print("Matching movies List :: ", movies_list)

	show_details = {}
	theatres_list = set()
	Baseurl = "https://in.bookmyshow.com/buytickets/"
	Curdate = getDate()
	Curtime = getTime()


	for movie_info in movies_list: 
		url = Baseurl + movie_info[0].replace(' ', '-').lower() + "-" + city.lower() + "/movie-" + city.lower() + "-" + movie_info[1] + "/" + Curdate
		print("\n\nURL:: " + url + "\n\n")
		bms_client.set_url(url)
		data = bms_client.get_details()
		for row in data:
			theatre_name = row['theatre_name']
			theatres_list.add(theatre_name)
			if theatre_name not in show_details:
				show_details[theatre_name] = []
			if row['time_code'] > Curtime:
				temp = {}
				temp['time'] = row['show_time']
				temp['min_price'] = row['min_price']
				temp['max_price'] = row['max_price']
				show_details[theatre_name].append(temp)

	# Slot value may be present here
	multiplex = getSlotValue(intent, 'MULTIPLEX')
	if multiplex != -1:
		multiplex = multiplex.lower()
		pass
	else:
		"""
		See this now : 
		https://developer.amazon.com/docs/custom-skills/dialog-interface-reference.html#elicitslot
		"""
		multi_list = set()
		outputSpeech = ""
		for theatre in theatres_list:
			sim = False
			for multi in multi_list:
				if similar(multi, theatre[: theatre.find(":")]):
					sim = True
					break
			if not sim:
				multi_list.add(theatre[: theatre.find(":")])

		i = 0
		for multi in multi_list:
			outputSpeech += multi 
			if i < len(multi_list) - 1:
				outputSpeech += ", "
			if i == len(multi_list) - 2:
				outputSpeech += "and "
			i += 1

		return {
			"version": "1.0",
			"sessionAttributes": {},
			"response": {
			"outputSpeech": {
				"type": "PlainText",
				"text": "These are the multiplex" + ("es" if len(multi_list) > 1 else "") + " " + outputSpeech + ". Please select one out of these."
				# outputSpeech contains the list of options I want the user to select from
			},
			"shouldEndSession": False,
			"directives": [
				{
					"type": "Dialog.ElicitSlot",
					"slotToElicit": "MULTIPLEX",
					"updatedIntent": {
						"name": "GetMovieDetails",
						"confirmationStatus": "NONE",
						"slots": {
							"CITY" : {
								"name" : "CITY",
								"confirmationStatus" : "NONE",
								"value" : city # this is already filled, it is just anti-capitalised 
							},
							"NAME" : {
								"name" : "NAME",
								"confirmationStatus" : "NONE",
								"value" : movie_name # this is already filled, it is just anti-capitalised 
							},
							"MULTIPLEX" : {
								"name" : "MULTIPLEX",
								"confirmationStatus" : "NONE",
							}
						}
					}
				}
			]
		}
	}


# Skeleton of result
# show_details{
#   details : [
#       {
#           time : 
#           min_price : 
#           max_price : 
#       },
#       {
#           time : 
#           min_price : 
#           max_price : 
#       },
#   ]
# }


def getOSandCC(results):
	outputSpeech = ""
	cardContent = ""
	i = 0
	for result in results:
		outputSpeech += result[0].strip()
		cardContent += result[0].strip() + "\n"
		if i < len(results) - 1 and len(results) > 0:
			outputSpeech += ", "
		if i == len(results) - 2 and i != 0 :
			outputSpeech += " and "
		i += 1

	return outputSpeech, cardContent


def similar(a, b):
	total = len(b)
	a = a.split(' ')
	b = b.split(' ')
	a = [element.lower() for element in a]
	b = [element.lower() for element in b]
	a = [filter(str.isalnum, element) for element in a]
	b = [filter(str.isalnum, element) for element in b]
	
	matches = 0
	for i in b:
		for j in a:
			if SequenceMatcher(None, i, j).ratio() > 0.8 :
				matches += len(j)
				break
	if (total != 0 and float(matches)/total > 0.3):
		return True

	# print(matches, total, (float(matches)/total))
	return False



def getDate():
	d = datetime.now()
	temp = "20"
	temp += d.strftime("%y%m%d")
	print(temp)
	return temp

def getTime():
	d = datetime.now()
	temp = d.strftime("%H%M")
	print(temp)
	return temp


def response_plain_text(output, endsession, attributes, title, cardContent, repromt = ""):
	print("\n")
	print(output)
	print("\n")
	""" create a simple json plain text response  """
	return {
		'version'   : '1.0',
		'response'  : {
			'shouldEndSession'  : endsession,
			'outputSpeech'  : {
				'type'      : 'PlainText',
				'text'      : output
			},
			'card' : {
				'type' : 'Simple',
				'title' : title,
				'content' : cardContent    
			},
			'repromt' : {
				'outputSpeech' : {
					'type' : 'PlainText',
					'text' : repromt
				}
			}
		},
		'sessionAttributes' : attributes
	}


def getSlotValue(intent, slot):
	if 'slots' in intent:
		if slot in intent['slots']:
			if 'value' in intent['slots'][slot]:
				return intent['slots'][slot]['value']
	
	return -1


def getRandom(messages):
	return messages[random.randint(0, len(messages) - 1)] 


def getWelcomeMessage():
	Messages = [
		"Namaste, What can I do for you?",
		"Looking for movies? I can help you there.",
		"Please put me on work. I can find movies for you."
	]
	return getRandom(Messages)

def do_help():
	Messages = [
		"You can say 'tell me about the upcoming movies'",
		"You can ask for movies now showing",
		"You can ask for a movies showing in particular language"
	]
	return response_plain_text(
			getRandom(Messages),
			False,
			{},
			"Flick - Get the movies you want",
			"What can I do for you?",
			"I would love to hear from you"
		)

def do_stop():
	Messages = [
		"Good Bye!!"
	]
	return response_plain_text(
			getRandom(Messages),
			True,
			{},
			"TATA",
			"We hope to see you again.",
			"Is there anything I can do for you?"
		)



def dialog_response(attributes, endsession):

	return {
		'version': '1.0',
		'sessionAttributes': attributes,
		'response':{
			'directives': [
				{
					'type': 'Dialog.Delegate'
				}
			],
			'shouldEndSession': endsession
		}
}


# else:
		#   try:
		#       coming_soon = bms_client.get_coming_soon()
		#   except Exception as e:
		#       print(e.args)
		#       print(type(e))
		#       return response_plain_text(
		#               "Something went wrong, I'm terribly sorry",
		#               True,
		#               {},
		#               "Error",
		#               "I could not process your request at the moment.",
		#               "Please try again. I would love to hear from you again"
		#           )
		#   else:
		#       if movieName != -1:
		#           for movie_info in coming_soon:
		#               if jellyfish.damerau_levenshtein_distance(movieName.lower(), movie_info[0].lower()) > 0.8:
		#                   result.append(movie_info)
		#       else:
		#           result.append(movie_info)



