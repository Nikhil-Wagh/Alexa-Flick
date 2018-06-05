"""
These are the intents which this skill supports and the respective slots

getMoviesNowShowing                                   
  - language 
  - city  

# This is put on hold
getMoviesComingSoon 
	- language
	- city

GetMovieDetails
  - Movie name
  - city
  - theatre

# This is put on hold
areSeatsAvailable
  - movie name
  - ShowTime
  - city

# This is put on hold
getTheatreList
  - city                                              
"""

"""
To test it try this on your terminal
python-lambda-local -f lambda_handler -t 10 lambda_function.py ./events/event.json
replace event.json with any one of the events in the events folder
"""

import re
import requests
import random
from datetime import datetime
import time
from difflib import SequenceMatcher

class BookMyShowClient(object):
	NOW_SHOWING_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"Filter Impression:category\\\/now showing"},"products":\[{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}\]}}}'
	COMING_SOON_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"category\\\/coming soon"},"products":{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}}}}'
	DETAILED_REGEX = '{"VenueCode":"(.*?)","EventCode":"(.*?)","SessionId":(.*?),"ShowTime":"(.*?)","ShowTimeCode":"(.*?)","MinPrice":"(.*?)","MaxPrice":"(.*?)","Availability":"(.*?)","CutOffFlag":"(.*?)","ShowDateTime":"(.*?)","CutOffDateTime":"(.*?)","BestBuy":"(.*?)","ShowDateCode":"(.*?)","IsAtmosEnabled":"(.*?)","SessionUnpaidFlag":"(.*?)","SessionUnpaidQuota":"(.*?)","BestAvailableSeats":(.*?),"Attributes":"(.*?)","SessionCodFlag":"(.*?)","SessionCodQuota":"(.*?)","SessionCopFlag":"(.*?)","SessionCopQuota":"(.*?)","SessionPopUpDesc":"(.*?)","Class":"(.*?)"}'
	VENUE_REGEX = '{"VenueCode":"(.*?)","VenueName":"(.*?)","VenueAdd":"(.*?)","VenueLegends":"(.*?)","VenueOffers":"(.*?)","SessCount":"(.*?)","AllowSales":"(.*?)","CompCode":"(.*?)","Lat":"(.*?)","Lng":"(.*?)","SubRegCode":"(.*?)","SubRegName":"(.*?)","SubRegSeq":"(.*?)","VenueApp":"(.*?)","IsNewCinema":"(.*?)","IsFoodSales":"(.*?)","IsMultiplex":"(.*?)","IsFullSeatLayout":"(.*?)","Message":"(.*?)","MessageType":"(.*?)","MessageTitle":"(.*?)","CinemaUnpaidFlag":"(.*?)","MTicket":"(.*?)","PopUpDescription":"(.*?)","IsFullLayout":"(.*?)","CinemaCodFlag":"(.*?)","CinemaCopFlag":"(.*?)","TicketCancellation":"(.*?)","VenueInfoMessage":"(.*?)"}'
	

	def __init__(self, location):
		self.__location = location.lower()
		self.__url = "https://in.bookmyshow.com/%s/movies" % self.__location
		self.__html = None

	def set_url(self, url):
		self.__url = url
		self.__html = None

	def __download(self):
		req = requests.get(self.__url, headers={'User-Agent' : "Magic Browser"})
		
		print "Downloaded from ::", req.url
		print "Status Code::", req.status_code
		print "\n\n"

		html = req.text
		return html.encode('ascii', 'ignore')

	def compare(self, left, right, movie_name, text) : 
		i = left
		j = 0
		while i < right and j < len(movie_name): 
			if not movie_name[j].isalnum() : 
				j += 1
			if not text[i].isalnum() : 
				i += 1
			if (j < len(movie_name) and i < right) and (movie_name[j].isalnum() and text[i].isalnum()) : 
				if movie_name[j].lower() != text[i].lower() : 
					return False
				else : 
					i += 1
					j += 1

		return True

	def get_now_showing(self):
		if not self.__html:
			self.__html = self.__download()
		now_showing = re.findall(self.NOW_SHOWING_REGEX, self.__html)

		"""
		This is done to add the buy URL to now_showing tuple 
		"""
		found = set()
		for index in re.finditer("/buytickets/", self.__html) : 
			left = index.start() 
			right = self.__html.find(self.__location, left + 1)
			name = self.__html[left:right]
			
			if name not in found : 
				# print left, right, name
				found.add(name)
				for i in range(0, len(now_showing)) : 
					if self.compare(left + len("/buytickets/"), right, now_showing[i][0], self.__html): 
						# Url added here
						now_showing[i] += ("https://in.bookmyshow.com" + self.__html[left:self.__html.find("\"", left + 1)], ) 
						break

		found.clear()

		image_urls = re.findall("data-src=\"(.*?)\"", self.__html)
		for url in image_urls : 
			left = url.find("/large/") + len("/large/")
			right = len(url) - 35 # 35 characters at the end do not contribute to the name of the movie
			name = url[left : right]
			print name, url, "\n"

			if name not in found : 
				found.add(name)
				for i in range(0, len(now_showing)) : 
					if self.compare(left, right, now_showing[i][0], url) :
						now_showing[i] += ("https:" + url, )
						break
		
		for row in now_showing:
			print row, "\n"
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
			venue_list[row[0]] = row[1]		# row[0] is venue code and row[1] is the venue name

		details = re.findall(self.DETAILED_REGEX, self.__html)
		show_list = []
		for row in details:
			current = {}
			current['theatre_name'] = venue_list[row[0]]    # add theatre name
			current['show_time'] = row[3]                   # add time
			current['time_code'] = row[4]                   # add time code for eg '1700'
			current['min_price'] = row[5]					# For eg : '60.00'
			current['max_price'] = row[6]					# For eg : '70.00'
			current['class'] = row[-1]                      # Morning, afternoon
			show_list.append(current)
		return show_list


def lambda_handler(event, context):
	if event['request']['type'] == "LaunchRequest":
		return on_launch(event, context)
	elif event['request']['type'] == 'IntentRequest':
		return on_intent(event)
	elif event['request']['type'] == 'SessionEndedRequest':
		return on_session_ended()
		

def on_launch(event, context):
	welcomeMessage = getWelcomeMessage()
	return response_plain_text(welcomeMessage, False, {}, "Welcome", welcomeMessage, "How can I help you?")


def on_intent(event):
	request = event['request']
	intent = request['intent']
	intent_name = request['intent']['name']

	if intent_name == "AMAZON.HelpIntent":
		return do_help()
	elif intent_name == "AMAZON.StopIntent":
		return do_stop()
	elif intent_name == "AMAZON.CancelIntent":
		return do_stop()

	# DialogState has to be returned only for non built-in intents
	if 'dialogState' in request:
		if request['dialogState'] == "STARTED" or request['dialogState'] == "IN_PROGRESS":
			return dialog_response(request['dialogState'], False)

	if intent_name == 'GetMoviesNowShowing':
		return GetMoviesNowShowing(intent)
	elif intent_name == 'GetMovieDetails':
		return GetMovieDetails(event)
	else : 
		print "Incorrect response do help"
		return do_help()

# Returns a response to lambda_handler, which contains a list of movies showing in the your area and in your given dialect 
def GetMoviesNowShowing(intent):
	start = time.time()
	print_now("Started at ::", start)

	city = getSlotValue(intent, 'CITY').lower()
	language = getSlotValue(intent, 'LANGUAGE').lower()	

	print "User's City:", city, ",\nUser's Language:", language
	result = []
	
	bms_client = BookMyShowClient(city)
	try:
		now_showing = bms_client.get_now_showing()
		print_now("Recieved data from remote site at ::", start)
	except Exception as e: 
		print e.args 
		print type(e) 
		return response_plain_text(
				"Something went wrong, I'm terribly sorry. Please try again.",
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

	print_now("Response generated at ::", start)
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
				"Bummer, I couldn't find anything for that language. There may be movies showing in other languages, please try that.",
				True,
				{},
				"Nothing to show",
				"No movies showing right now.\nTry changing the language you want to watch your movie in."
			)

def print_now(s, start) : 
	now = time.time()
	print s, (now - start)*1000, "milliseconds\n"


# url = https://in.bookmyshow.com/buytickets/bharat-ane-nenu-pune/movie-pune-ET00059033-MT/20180421
def GetMovieDetails(event):
	intent = event['request']['intent']
	start = time.time()
	
	city = getSlotValue(intent, 'CITY').lower()
	movie_name = getSlotValue(intent, 'NAME').lower()
	movie_name = movie_name.encode('ascii', 'ignore')
	print_now("Started at ::", start)
	

			'''
		{
			"phase" : <digit>,
			"similar_movies" = List[],
			"theatres_showing_movie" = List[]
		}
		'''
		


	# PHASE 1
	# Downloading front page where all movies briefing is done.
	# this is taking a lot of time
	bms_client = BookMyShowClient(city)
	try:
		now_showing = bms_client.get_now_showing()
	except Exception as e: # Error
		print "Error in retrieving data for GetMovieDetails - ", city, movie_name
		print e.args 
		print type(e) 
		return response_plain_text(
				"Something went wrong, I'm terribly sorry",
				True,
				{},
				"Error",
				"I could not process your request at the moment.",
				"Please try again. I would love to hear from you again"
			)

	print_now("Gathered all movies data in::", start)

	movies_list = []
	for movie in now_showing:
		if similar(movie[0], movie_name) : 
			movies_list.append(movie)

	print "Matching movies List :: ", movies_list
	print_now("Movie list created at ::", start)


	# Download pages of specific movies, all those whose name is similar to what user just said
	all_show_details = {}
	theatres_list = set()
	Curdate = getDate()
	Curtime = getTime()

	all_data = []
	for movie_info in movies_list: 
		url = movie_info[6]
		# url = Baseurl + movie_info[0].replace(' ', '-').lower() + "-" + city.lower() + "/movie-" + city.lower() + "-" + movie_info[1] + "/" + Curdate
		# print "URL:: " + url + "\n\n"
		bms_client.set_url(url)
		data = bms_client.get_details()
		for row in data:
			theatres_list.add(row['theatre_name'])
			all_data.append(row)

	print "List of Theatres : ", theatres_list, "\n\n" 
	print_now("Got all data from remote site at::", start)

	# PHASE 2
	# Slot value may be present here
	multiplex = getSlotValue(intent, 'MULTIPLEX')
	if multiplex != -1:
		accepted_theatre_name = -1
		if len(theatres_list) > 2 : 
			accepted_theatre_name = getSlotValue(intent, 'THEATRE')
			if accepted_theatre_name == -1 : 
				return dialog_elicit_slot()

		multiplex = multiplex.encode('ascii', 'ignore')
		multiplex = multiplex.lower()		
		show_details = dict()
		"""
			show_details = {
				"theatre_name" : [
					There may be a number of shows in the same theatre at different times
					{
						"show_time" : <string>,
						"min_price" : <float>,
						"max_price"	: <float>
					},
					{
						"show_time" : <string>,
						"min_price" : <float>,
						"max_price"	: <float>
					},
					.
					.
					.
				]
			}
		"""	
		print "MULTIPLEX", multiplex 
		for row in all_data: 
			theatre_name = row['theatre_name']
			print theatre_name
			if similar(multiplex, theatre_name[: theatre_name.find(":")]) :
				temp = {}
				temp['show_time'] = row['show_time']
				temp['min_price'] = row['min_price']
				temp['max_price'] = row['max_price']
				if theatre_name not in show_details:
					show_details[theatre_name] = []	
				show_details[theatre_name].append(temp)

		print "All required details", show_details
		
		outputSpeech = ""
		cardContent = ""
		i = 0 
		for element, values in show_details.iteritems() : 
			theatre_name = element[element.find(":") + 2: element.rfind(",")]
			outputSpeech += "At " + theatre_name + ", "
			cardContent += element + ":: "
			i = 0
			for value in values : 
				outputSpeech += value['show_time']
				cardContent += value['show_time'] + " (" + value['min_price'] + " Rs - " + value['max_price'] + " Rs)"
				if i < len(values) - 1:
					outputSpeech += ", "
					cardContent += ", "
				if i == len(values) - 2:
					outputSpeech += "and "
					cardContent += "and " 
				i += 1
			outputSpeech += ". "
			cardContent += "\n"

		print_now("Result generated at ::", start)
		output = ""
		if len(show_details) > 0 : 
			output = "Here are the show timings ... " + outputSpeech
		else : 
			output = "Sorry I couldn't find anything for " + movie_name + " at " + multiplex
		return response_plain_text(
				output,
				True, 
				{},
				"Show Details",
				cardContent
			)

	else:
		"""
		See this now : 
		https://developer.amazon.com/docs/custom-skills/dialog-interface-reference.html#elicitslot
		"""
		outputSpeech = ""
		multi_list = set()
		for theatre in theatres_list:
			sim = False
			# check for already
			for multi in multi_list:
				if similar(multi, theatre[: theatre.find(":")]):
					sim = True
					break
			if not sim:
				multi_list.add(theatre[: theatre.find(":")])

		if len(multi_list) <= 0: 
			return response_plain_text(
					"Sorry couldn't find anything for " + movie_name + " in " + city + ". Please try again for different movie.",
					True, 
					{},
					"No results found",
					"Could not find any available multiplexes for " + movie_name
				)

		i = 0
		for multi in multi_list:
			outputSpeech += multi 
			if i < len(multi_list) - 1:
				outputSpeech += ", "
			if i == len(multi_list) - 2:
				outputSpeech += "and "
			i += 1

		print_now("Result generated at ::", start)
		output = "These are the multiplex" + ("es" if len(multi_list) > 1 else "") + ", " + outputSpeech + ". Please select one out of these."
		return dialog_elicit_slot(output, city, movie_name)


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
			outputSpeech += "and "
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

	return False


def getSlotValue(intent, slot):
	if 'slots' in intent:
		if slot in intent['slots']:
			if intent['slots'][slot].has_key('resolutions') :
				if intent['slots'][slot]['resolutions'].has_key('resolutionsPerAuthority') : 
					if len(intent['slots'][slot]['resolutions']['resolutionsPerAuthority']) > 0 :
						resolutions = intent['slots'][slot]['resolutions']['resolutionsPerAuthority'][0]
						if resolutions.has_key('values') : 
							if len(resolutions['values']) > 0 :
								value = resolutions['values'][0]
								if value.has_key('value') :
									if value['value'].has_key('name') and len(value['value']['name']) > 0: 
										return value['value']['name']
			if 'value' in intent['slots'][slot] and len(intent['slots'][slot]['value']) > 0:
				return intent['slots'][slot]['value']
	
	return -1

def getRandom(messages):
	return messages[random.randint(0, len(messages) - 1)] 

def getDate():
	d = datetime.now()
	temp = "20"
	temp += d.strftime("%y%m%d")
	return temp

def getTime():
	d = datetime.now()
	temp = d.strftime("%H%M")
	return temp

def getWelcomeMessage():
	# TODO: Improve this
	Messages = [
		"Namaste, What can I do for you?",
		"Looking for movies? I can help you there.",
		"Please put me on work. I can find movies for you."
	]
	return getRandom(Messages)

def do_help():
	# TODO: Improve this
	Messages = [
		"You can say 'tell me about the movies showing near me'",
		"You can ask for 'movies now showing'",
		"You can ask for 'movies showing in english'"
	]
	return response_plain_text(
			getRandom(Messages) + ", or you can say 'I want to watch a movie'",
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
	# TODO: Improve this
	return response_plain_text(
			getRandom(Messages),
			True,
			{},
			"TATA",
			"We hope to see you again.",
			"Is there anything I can do for you?"
		)

# **************  Responses  ******************** #

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


def dialog_elicit_slot(output, slotToElicit, city_name, movie_name, multiplex = None, theatre_name = None):
	print output, "\n"
	return {
		"version": "1.0",
		"sessionAttributes": {},
		"response": {
			"outputSpeech": {
				"type": "PlainText",
				"text": output
			},
			"shouldEndSession": False,
			"directives": [
				{
					"type": "Dialog.ElicitSlot",
					"slotToElicit": slotToElicit,
					"updatedIntent": {
						"name": "GetMovieDetails",
						"confirmationStatus": "NONE",
						"slots": {
							"CITY": {
								"name": "CITY",
								"confirmationStatus": "NONE",
								"value": city_name
							},
							"NAME": {
								"name": "NAME",
								"confirmationStatus": "NONE",
								"value": movie_name
							},
							"MULTIPLEX": {
								"name": "MULTIPLEX",
								"confirmationStatus": "NONE",
								"value" : multiplex
							},
							"THEATRE": {
								"name": "THEATRE",
								"confirmationStatus": "NONE",
								"value" : theatre_name
							}
						}
					}
				}
			]
		}
	}


