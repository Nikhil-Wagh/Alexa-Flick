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
		
	if not attributes.has_key("all_data"):
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

		# Set attributes['all_data'] value to be send with output at every response
		attributes['all_data'] = all_data

		print "List of Theatres : ", theatres_list, "\n\n" 
		print_now("Got all data from remote site at::", start)


	if attributes.has_key("all_data"):
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
			print "MULTIPLEX", ui_multiplex 
			
			show_details = getShowDetails(all_data, ui_multiplex)

			ui_theatre = getSlotValue(intent, 'THEATRE')
			if ui_theatre != -1:
				for theatre, shows in show_details.iteritems():
					theatre_name = theatre[theatre.find(":") + 2: theatre.rfind(",")]
					if not similar(theatre_name, ui_theatre):
						del show_details[theatre]
			else:
				multiplex_filtered_theatres = set()
				for theatre, shows in show_details.iteritems():
					multiplex_filtered_theatres.add(row['theatre_name'])

				if len(multiplex_filtered_theatres) > 3:
					i = 0
					outputSpeech = ""
					for theatre in multiplex_filtered_theatres:
						outputSpeech += theatre
						if i < len(multiplex_filtered_theatres) - 1:
							outputSpeech += ", "
						if i == len(multiplex_filtered_theatres) - 2:
							outputSpeech += "and "
						i += 1

					print_now("List of Available Theatres generated at ::", start)
					output = "These are the theatre" + ("s" if len(multi_list) > 1 else "") + ", " + outputSpeech + ". Please select one out of these."
					# TODO: this elicit_slot syntax is not correct
					return dialog_elicit_slot(output, city, movie_name)

			"""
			If the count of total number of available theatres is more than 3 or user specifically wants to see 
			in some particular theatre (and he has given its name explictly), then the show_details has to be filtered 
			with respect to the choices.

			Below shown results are completely filtered
			"""
			print "All required details", show_details
		
			outputSpeech = ""
			cardContent = ""
			i = 0 
			for theatre, shows in show_details.iteritems() : 
				theatre_name = theatre[theatre.find(":") + 2: theatre.rfind(",")]
				outputSpeech += "At " + theatre_name + ", "
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
				output = "Sorry I couldn't find anything for " + movie_name + " at " + multiplex
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
				# check for already
				for multi in available_multiplexes:
					if similar(multi, theatre[: theatre.find(":")]):
						sim = True
						break
				if not sim:
					available_multiplexes.append(theatre[: theatre.find(":")])

			if len(available_multiplexes) > 3 or len(available_theatres) > 3: 
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
				return dialog_elicit_slot(output, city, movie_name)

			else :
				outputSpeech = ""
				cardContent = ""
				for multiplex in available_multiplexes:
					show_details = getShowDetails(all_data, multiplex)
					for theatre, shows in show_details.iteritems(): 
						theatre_name = theatre[theatre.find(":") + 2: theatre.rfind(",")]
						outputSpeech += "At " + theatre_name + ", "
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
		if similar(multiplex, theatre_name[: theatre_name.find(":")]) :
			temp = {}
			temp['show_time'] = row['show_time']
			temp['min_price'] = row['min_price']
			temp['max_price'] = row['max_price']
			if theatre_name not in show_details:
				show_details[theatre_name] = []	
			show_details[theatre_name].append(temp)

	return show_details
