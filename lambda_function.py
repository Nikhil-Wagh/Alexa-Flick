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
from BMS import BookMyShowClient


def lambda_handler(event, context):
	if event['request']['type'] == "LaunchRequest":
		return on_launch(event, context)
	elif event['request']['type'] == 'IntentRequest':
		return on_intent(event)
	elif event['request']['type'] == 'SessionEndedRequest':
		return do_stop()
		

def on_launch(event, context):
	welcomeMessage = getWelcomeMessage()
	return response_plain_text(welcomeMessage, False, {}, "Welcome", welcomeMessage, "How can I help you?")


def elicit_slot(attributes, outputSpeech, slotToElicit, intent_name, confirmationStatus, slots):
	return {
		"version": "1.0",
		"sessionAttributes": attributes,
		"response": {
			"outputSpeech": {
				"type": "PlainText",
				"text": outputSpeech
			},
			"shouldEndSession": False,
			"directives": [
				{
					"type": "Dialog.ElicitSlot",
					"slotToElicit": slotToElicit,
					"updatedIntent": {
						"name": intent_name,
						"confirmationStatus": confirmationStatus,
						"slots": slots
					}
				}
			]
		}
	}

def updateSlots(original, custom):
	slots = {}
	for slot_name, slot in original.items():
		temp = dict()
		temp['name'] = slot_name
		temp['value'] = custom[slot_name]['value'] if slot_name in custom else ""
		print(temp)
		slots[slot_name] = temp
	return slots

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
		if intent['confirmationStatus'] == "DENIED":
			return {
				'version': '1.0',
				'sessionAttributes': {},
				'response':{
					'directives': [
						{
							'type': 'Dialog.Delegate',
							'updatedIntent' : {
								'name': intent_name,
								'confirmationStatus': 'NONE',
								'slots': updateSlots(intent['slots'], {})
							}
						}
					],
					'shouldEndSession': False
				}
			}
		elif request['dialogState'] == "STARTED" or request['dialogState'] == "IN_PROGRESS":
			return dialog_response(request['dialogState'], False)
			

	if intent_name == 'GetMoviesNowShowing':
		return GetMoviesNowShowing(intent)
	elif intent_name == 'GetMovieDetails':
		return GetMovieDetails(event)
	elif intent_name == "AMAZON.RepeatIntent":
		return do_repeat(event)
	else : 
		print("Incorrect response do help")
		return do_help()

# Returns a response to lambda_handler, which contains a list of movies showing in the your area and in your given dialect 
def GetMoviesNowShowing(intent):
	start = time.time()
	print_now("Started at ::", start)

	city = getSlotValue(intent, 'CITY').lower()
	language = getSlotValue(intent, 'LANGUAGE').lower()	

	print("User's City:", city, ",\nUser's Language:", language)
	result = []
	
	bms_client = BookMyShowClient(city)
	try:
		now_showing = bms_client.get_now_showing()
		print_now("Recieved data from remote site at ::", start)
	except Exception as e: 
		print(e.args) 
		print(type(e)) 
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
	print(s, (now - start)*1000, "milliseconds\n")


# url = https://in.bookmyshow.com/buytickets/bharat-ane-nenu-pune/movie-pune-ET00059033-MT/20180421
def GetMovieDetails(event) : 
	start = time.time()
	print_now("Started at ::", start)
	
	intent = event['request']['intent']
	city = getSlotValue(intent, 'CITY').lower()
	movie_name = getSlotValue(intent, 'NAME').lower()
	movie_name = movie_name.encode('ascii', 'ignore')
	
	attributes = dict()
	if 'attributes' in event['session']: 
		attributes = event['session']['attributes']
		
	if 'all_data' not in attributes:
		bms_client = BookMyShowClient(city)
		try:
			now_showing = bms_client.get_now_showing()
		except Exception as e: # Error
			print("Error in retrieving data for GetMovieDetails - ", city, movie_name)
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

		print_now("Gathered all movies data in::", start)

		movies_list = []
		for movie in now_showing:
			if similar(movie[0], movie_name) : 
				movies_list.append(movie)

		print("Matching movies List :: ", movies_list)
		print_now("Movie list created at ::", start)

		# Download pages of specific movies, all those whose name is similar to what user just said
		all_data = []
		for movie_info in movies_list: 
			url = movie_info[6]
			# url = Baseurl + movie_info[0].replace(' ', '-').lower() + "-" + city.lower() + "/movie-" + city.lower() + "-" + movie_info[1] + "/" + Curdate
			# print "URL:: " + url + "\n\n"
			bms_client.set_url(url)
			data = bms_client.get_details()
			# print "DATA", data
			for row in data:
				all_data.append(row)

		# print all_data

		# Set attributes['all_data'] value to be send with output at every response
		attributes['all_data'] = all_data
		print_now("Got all data from remote site at::", start)


	# all_data is collected (either by previous call or by present call)
	all_data = attributes['all_data']
	if len(all_data) == 0: 
		return response_plain_text(
				"Sorry couldn't find anything for " + movie_name + " in " + city + ". Please try again for different movie.",
				True, 
				{},
				"No results found",
				"Could not find any available multiplexes for " + movie_name
			)

	ui_multiplex = getSlotValue(intent, 'MULTIPLEX')
	if ui_multiplex != -1:
		ui_multiplex = ui_multiplex.encode('ascii', 'ignore')
		ui_multiplex = ui_multiplex.lower()		
		
		show_details = getShowDetails(all_data, ui_multiplex)

		ui_theatre = getSlotValue(intent, 'THEATRE')

		if ui_theatre != -1:
			ui_theatre = ui_theatre.encode('ascii', 'ignore')
			ui_theatre = ui_theatre.lower()
			
			for theatre in show_details.keys():
				theatre_name = theatre[theatre.find(":") + 2: theatre.rfind(",")]
				if not similar(theatre_name.lower(), ui_theatre):
					del show_details[theatre]
		else:
			multiplex_filtered_theatres = set()
			for theatre, shows in show_details.items():
				multiplex_filtered_theatres.add(theatre)
			print("Number of theatres that are filtered with respect to MULTIPLEX", len(multiplex_filtered_theatres))

			if len(multiplex_filtered_theatres) > 3:
				i = 0
				outputSpeech = ""
				for theatre in multiplex_filtered_theatres:
					last = theatre.rfind(",")
					if last != -1 :
						outputSpeech += theatre[0 if theatre.find(":") == -1 else (theatre.find(":") + 2):last].replace(",", " ")
					else:
						outputSpeech += theatre[0 if theatre.find(":") == -1 else (theatre.find(":") + 2):].replace(",", " ")
					if i < len(multiplex_filtered_theatres) - 1:
						outputSpeech += ", "
					if i == len(multiplex_filtered_theatres) - 2:
						outputSpeech += "and "
					i += 1

				print_now("List of Available Theatres generated at ::", start)
				output = "These are the theatre" + ("s" if len(multiplex_filtered_theatres) > 1 else "") + ", " + outputSpeech + ". Please select one out of these."
				# TODO: this elicit_slot syntax is not correct
				return dialog_elicit_slot(output, 'THEATRE', city, movie_name, attributes, ui_multiplex)

		"""
		If the count of total number of available theatres is more than 3 or user specifically wants to see 
		in some particular theatre (and he has given its name explictly), then the show_details has to be filtered 
		with respect to the choices.

		Below shown results are completely filtered
		"""
	
		outputSpeech = ""
		cardContent = ""
		i = 0 
		for theatre, shows in show_details.items() : 
			# theatre_name = theatre[: theatre.find(",") if theatre.find(",") != -1 else len(theatre)]
			last = theatre.rfind(",")
			if last != -1 :
				theatre_name = theatre[:last]
			else:
				theatre_name = theatre
			# theatre_name = theatre[theatre.find(":") + 2: theatre.rfind(",")]
			outputSpeech += "At " + theatre_name.replace(",", " ") + ", "
			cardContent += theatre + ":: "
			i = 0
			for current_show in shows : 
				outputSpeech += current_show['show_time']
				cardContent += current_show['show_time'] + " (" + current_show['min_price'] + " Rs - " + current_show['max_price'] + " Rs)"
				if i < len(shows) - 1:
					outputSpeech += ", "
					cardContent += ", "
				if i == len(shows) - 2:
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
			output = "Sorry I couldn't find anything for " + movie_name + " at " + ui_multiplex
		return response_plain_text(
				output,
				True, 
				attributes,
				"Show Details",
				cardContent
			)


	else:
		# All available_theatres without filtering
		available_theatres = set()
		for row in all_data:
			available_theatres.add(row['theatre_name'])

		available_multiplexes = []
		for theatre in available_theatres:
			sim = False
			last = theatre.find(":")
			if last == -1:
				last = len(theatre)
			# check for already
			for multi in available_multiplexes:
				if similar(multi, theatre[: last]):
					sim = True
					break
			if not sim:
				available_multiplexes.append(theatre[: last])

		if len(available_multiplexes) > 2: 
			i = 0
			outputSpeech = ""
			for multi in available_multiplexes:
				outputSpeech += multi 
				if i < len(available_multiplexes) - 1:
					outputSpeech += ", "
				if i == len(available_multiplexes) - 2:
					outputSpeech += "and "
				i += 1

			print_now("List of Available Multiplexes generated at ::", start)
			output = "These are the multiplex" + ("es" if len(available_multiplexes) > 1 else "") + ", " + outputSpeech + ". Please select one out of these."
			return dialog_elicit_slot(output, 'MULTIPLEX', city, movie_name, attributes)

		else :
			outputSpeech = ""
			cardContent = ""
			for multiplex in available_multiplexes:
				show_details = getShowDetails(all_data, multiplex)
				for theatre, shows in show_details.items(): 
					last = theatre.rfind(",")
					if last != -1 :
						theatre_name = theatre[:last]
					else:
						theatre_name = theatre
					outputSpeech += "At " + theatre_name.replace(","," ") + ", "
					cardContent += theatre + ":: "
					i = 0
					for current_show in shows : 
						outputSpeech += current_show['show_time']
						cardContent += current_show['show_time'] + " (" + current_show['min_price'] + " Rs - " + current_show['max_price'] + " Rs)"
						if i < len(shows) - 1:
							outputSpeech += ", "
							cardContent += ", "
						if i == len(shows) - 2:
							outputSpeech += "and "
							cardContent += "and " 
						i += 1
					outputSpeech += ". "
					cardContent += "\n"

			print_now("Result generated at ::", start)
			output = ""
			if len(outputSpeech) > 0 : 
				output = "Here are the show timings ... " + outputSpeech
			else : 
				output = "Sorry I couldn't find anything for " + movie_name + "."
			return response_plain_text(
					output,
					True, 
					attributes,
					"Show Details",
					cardContent
				)
	
	
def getShowDetails(all_data, multiplex) :
	show_details = dict() 
	for row in all_data: 
		theatre_name = row['theatre_name']
		theatre_name = theatre_name.encode('ascii', 'ignore')
		if similar(multiplex, theatre_name[: theatre_name.find(":")]) :
			temp = {}
			temp['show_time'] = row['show_time']
			temp['min_price'] = row['min_price']
			temp['max_price'] = row['max_price']
			if theatre_name not in show_details:
				show_details[theatre_name] = []	
			show_details[theatre_name].append(temp)

	return show_details



def getOSandCC(results):
	outputSpeech = ""
	cardContent = ""
	i = 0
	for result in results:
		outputSpeech += result[0].strip()
		cardContent += result[0].strip()
		if i < len(results) - 1 and len(results) > 0:
			outputSpeech += ", "
			cardContent += ", "
		if i == len(results) - 2 and i != 0 :
			outputSpeech += "and "
			cardContent += "and "
		i += 1
		cardContent += "\n"
	outputSpeech += "."

	return outputSpeech, cardContent


def similar(a, b):
	total = len(b)
	if not isinstance(a, str):
		a = str(a, "utf-8")
	if not isinstance(b, str):
		b = str(b, "utf-8")
	a = a.split(' ')
	b = b.split(' ')
	a = [element.lower() for element in a]
	b = [element.lower() for element in b]
	
	matches = 0
	for i in b:
		for j in a:
			if SequenceMatcher(None, i, j).ratio() > 0.8 :
				matches += len(j)
				break
	if (total != 0 and float(matches)/total > 0.4):
		return True

	return False


def getSlotValue(intent, slot):
	if 'slots' in intent:
		if slot in intent['slots']:
			if 'resolutions' in intent['slots'][slot]:
			# if intent['slots'][slot].has_key('resolutions') :
				if 'resolutionsPerAuthority' in intent['slots'][slot]['resolutions']:
				# if intent['slots'][slot]['resolutions'].has_key('resolutionsPerAuthority') : 
					if len(intent['slots'][slot]['resolutions']['resolutionsPerAuthority']) > 0 :
						resolutions = intent['slots'][slot]['resolutions']['resolutionsPerAuthority'][0]
						if 'values' in resolutions:
						# if resolutions.has_key('values') : 
							if len(resolutions['values']) > 0 :
								value = resolutions['values'][0]
								if 'value' in value:
								# if value.has_key('value') :
									if 'name' in value['value'] and len(value['value']['name']) > 0:
									# if value['value'].has_key('name') and len(value['value']['name']) > 0: 
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
	return response_plain_text(
			getRandom(Messages),
			True,
			{},
			"TATA",
			"We hope to see you again.",
			"Is there anything I can do for you?"
		)

def do_repeat(event):
	if 'attributes' in event['session']: 
		attributes = event['session']['attributes']
		if 'lastSpeech' in attributes:
			return {
				'version'   : '1.0',
				'response'  : {
					'shouldEndSession'  : False,
					'outputSpeech'  : {
						'type'      : 'PlainText',
						'text'      : remove_special_characters(attributes['lastSpeech'])
					}
				},
				'sessionAttributes' : attributes
			}

# **************  Responses  ******************** #

def dialog_response(attributes, endsession, updatedIntent = None):
	return {
		'version': '1.0',
		'sessionAttributes': attributes,
		'response':{
			'directives': [
				{
					'type': 'Dialog.Delegate',
					'updatedIntent' : updatedIntent
				}
			],
			'shouldEndSession': endsession
		}
	}

def response_plain_text(output, endsession, attributes, title, cardContent, repromt = "How can I help you?"):
	print("\n", output, "\n") 
	print(title)
	print(cardContent)
	attributes['lastSpeech'] = output
	""" create a simple json plain text response  """
	return {
		'version'   : '1.0',
		'response'  : {
			'shouldEndSession'  : endsession,
			'outputSpeech'  : {
				'type'      : 'PlainText',
				'text'      : remove_special_characters(output)
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


def dialog_elicit_slot(output, slotToElicit, city_name, movie_name, attributes, multiplex = None, theatre_name = None, confirmationStatus = "CONFIRMED"):
	output = remove_special_characters(output)
	print(output, "\n")
	attributes['lastSpeech'] = output
	return {
		"version": "1.0",
		"sessionAttributes": attributes,
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
						"confirmationStatus": confirmationStatus,
						"slots": {
							"CITY": {
								"name": "CITY",
								"confirmationStatus": "CONFIRMED" if city_name != None else "NONE",
								"value": city_name
							},
							"NAME": {
								"name": "NAME",
								"confirmationStatus": "CONFIRMED" if movie_name != None else "NONE",
								"value": movie_name
							},
							"MULTIPLEX": {
								"name": "MULTIPLEX",
								"confirmationStatus": "CONFIRMED" if multiplex != None else "NONE",
								"value" : multiplex
							},
							"THEATRE": {
								"name": "THEATRE",
								"confirmationStatus": "CONFIRMED" if theatre_name != None else "NONE",
								"value" : theatre_name
							}
						}
					}
				}
			]
		}
	}

def remove_special_characters(s):
 	return re.sub(r'[^A-Za-z0-9.,?\'":() ]+', '', s)


def dialog_elicit_slot(output, slotToElicit, city_name, movie_name, attributes, multiplex = None, confirmationStatus = "CONFIRMED"):
	return {
		"version": "1.0",
		"sessionAttributes": attributes,
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
						"confirmationStatus": confirmationStatus,
						"slots": {
							"CITY": {
								"name": "CITY",
								"confirmationStatus": "CONFIRMED" if city_name != None else "NONE",
								"value": city_name
							},
							"NAME": {
								"name": "NAME",
								"confirmationStatus": "CONFIRMED" if movie_name != None else "NONE",
								"value": movie_name
							},
							"MULTIPLEX": {
								"name": "MULTIPLEX",
								"confirmationStatus": "CONFIRMED" if multiplex != None else "NONE",
								"value" : multiplex
							}
						}
					}
				}
			]
		}
	}


