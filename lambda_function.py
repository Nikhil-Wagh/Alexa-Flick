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

class BookMyShowClient(object):
	NOW_SHOWING_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"Filter Impression:category\\\/now showing"},"products":\[{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}\]}}}'
	COMING_SOON_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"category\\\/coming soon"},"products":{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}}}}'
	DETAILED_REGEX = '{"VenueCode":"(.*?)","EventCode":"(.*?)","SessionId":(.*?),"ShowTime":"(.*?)","ShowTimeCode":"(.*?)","MinPrice":"(.*?)","MaxPrice":"(.*?)","Availability":"(.*?)","CutOffFlag":"(.*?)","ShowDateTime":"(.*?)","CutOffDateTime":"(.*?)","BestBuy":"(.*?)","ShowDateCode":"(.*?)","IsAtmosEnabled":"(.*?)","SessionUnpaidFlag":"(.*?)","SessionUnpaidQuota":"(.*?)","BestAvailableSeats":(.*?),"Attributes":"(.*?)","SessionCodFlag":"(.*?)","SessionCodQuota":"(.*?)","SessionCopFlag":"(.*?)","SessionCopQuota":"(.*?)","SessionPopUpDesc":"(.*?)","Class":"(.*?)"}'
	VENUE_REGEX = '{"VenueCode":"(.*?)","VenueName":"(.*?)","VenueAdd":"(.*?)","VenueLegends":"(.*?)","VenueOffers":"(.*?)","SessCount":"(.*?)","AllowSales":"(.*?)","CompCode":"(.*?)","Lat":"(.*?)","Lng":"(.*?)","SubRegCode":"(.*?)","SubRegName":"(.*?)","SubRegSeq":"(.*?)","VenueApp":"(.*?)","IsNewCinema":"(.*?)","IsFoodSales":"(.*?)","IsMultiplex":"(.*?)","IsFullSeatLayout":"(.*?)","Message":"(.*?)","MessageType":"(.*?)","MessageTitle":"(.*?)","CinemaUnpaidFlag":"(.*?)","MTicket":"(.*?)","PopUpDescription":"(.*?)","IsFullLayout":"(.*?)","CinemaCodFlag":"(.*?)","CinemaCopFlag":"(.*?)","TicketCancellation":"(.*?)","VenueInfoMessage":"(.*?)"}'

	def __init__(self, location = 'Bengaluru'):
		self.__location = location.lower()
		self.__url = "https://in.bookmyshow.com/%s/movies" % self.__location
		self.__html = None

	def set_url(url):
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

	def get_details():
		if not self.__html:
			self.__html = self.__download()

		venue = re.findall(self.VENUE_REGEX, self.html)
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
	elif intent_name == 'GetMovieInfo':
		return GetMovieInfo(intent)
	elif intent_name == "AMAZON.HelpIntent":
		return do_help()
	elif intent_name == "AMAZON.StopIntent":
		return do_stop(attributes)
	elif intent_name == "AMAZON.CancelIntent":
		return do_stop()
	else:
		print ("Invalid Intent reply with help")
		do_help()


def GetMoviesNowShowing(intent):
	city = getSlotValue(intent, 'CITY')
	language = getSlotValue(intent, 'LANGUAGE')

	return response_plain_text("You have selected " + city + " and " + language + " language to see your movie", True, {}, "Hello", "Hello World")

	print(city, language)
	result = []
	if location != -1:
		bms_client = BookMyShowClient(location)
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
		else:
			if movieName != -1:
				for movie_info in now_showing:
					if similar(movieName.lower(), movie_info[0].lower()):
						result.append(movie_info)
			else:
				result.append(movie_info)
	else:
		attributes = {
			'Intent' : 'GetMovieList'
		}
		return response_plain_text("Please provide the location", False, attributes, "No location", "Found too many results", "I'm efficient if you provide me your location")

	if movieName != -1:
		showDetails = GetMovieDetails(bms_client, result, movieName, location)
		listTheatres = []
		for k in showDetails.iterkeys():
			listTheatres.append(k)

		print(listTheatres)
		print(showDetails)

	else:
		hello
		outputSpeech = "These are the movies which are showing in your area " 
		for r in result:
			outputSpeech += r[0] + " which is showed in dimension " + r[3] + " and the language is " + r[5]

		return response_plain_text(outputSpeech, False, {}, str(len(result)) + " movies showing", result)


#url = https://in.bookmyshow.com/buytickets/bharat-ane-nenu-pune/movie-pune-ET00059033-MT/20180421
def GetShowDetails(bms_client, movies_list, city):
	showDetails = {}
	Baseurl = "https://in.bookmyshow.com/buytickets/"
	Curdate = getDate()
	Curtime = getTime()
	for movie_info in movies_list: # No need to compare movie name as it is already compared above in GetMovieList
		url = Baseurl + movie_info[0].replace(' ', '-').lower() + "-" + city.lower() + "/movie-" + city.lower() + "-" + movie_info[1] + "/" + Curdate
		print("\n\nURL:: " + url + "\n\n")
		bms_client.set_url(url)
		data = bms_client.get_details()
		for row in data:
			theatre_name = row['theatre_name']
			if theatre_name not in showDetails:
				showDetails[theatre_name] = []
			if row['time_code'] > Curtime:
				temp = {}
				temp['time'] = row['time']
				temp['min_price'] = row['min_price']
				temp['max_price'] = row['max_price']
				showDetails[theatre_name].append(temp)

	return showDetails

	
	print("\n\n")   
	print(result)
	print("\n\n")


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


def similar(a, b):
	a = a.split(' ')
	b = b.split(' ')
	matches = 0
	for i in a:
		temp = b
		for j in temp:
			if i == j:
				matches += 1
				temp.remove(j)
				break
		total = len(b)
		if((total < 4 and (temp/total) > 0.5) or (temp/total > 0.7)):
			return True

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


def response_plain_text(output, endsession, attributes, title, cardContent, repromt):
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
			return intent['slots'][slot]['value']
	
	return -1


def getRandom(messages):
	return messages[random.randint(0, len(messages) - 1)] 


def getWelcomeMessage():
	Messages = [
		"Namaste, What can I do for you?",
		"Looking for movies? I'm can help you there.",
		"Please, put me on work. I can find movies for you."
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



