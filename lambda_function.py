import re
import urllib2
import jellyfish

class BookMyShowClient(object):
  NOW_SHOWING_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"Filter Impression:category\\\/now showing"},"products":\[{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}\]}}}'
  COMING_SOON_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"category\\\/coming soon"},"products":{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}}}}'

  def __init__(self, location = 'Bengaluru'):
    self.__location = location.lower()
    self.__url = "https://in.bookmyshow.com/%s/movies" % self.__location
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



def lambda_handler(event, context):
	if event['request']['type'] == "LaunchRequest":
		return on_launch(event, context)
	elif event['request']['type'] == 'IntentRequest':
		return on_intent(event['request'])
	elif event['request']['type'] == 'SessionEndedRequest':
		return on_session_ended()
		

def on_launch(event, context):
	return response_plain_text(getWelcomeMessage(), False, {}, "Welcome", getWelcomeMessage(), "How can I help you?")


def on_intent(request):
	intent = request['intent']
	intent_name = request['intent']['name']

	if 'session' in request:
		if 'attributes' in request['session']:
			if 'Intent' in request['session']['attributes']:
				function = request['session']['attributes']['Intent']
				if function == 'GetMovieList':
					GetMovieList(intent)

	if intent_name == 'GetMovieList':
		return GetMovieList(intent)


def GetMovieList(intent):
	movieName = getSlotValue(intent, 'NAME')
	location = getSlotValue(intent, 'LOCATION')
	when = getSlotValue(intent, 'WHEN')

	result = []
	if location != -1:
		bms_client = BookMyShowClient(location)
		if when != 'COMMING_SOON':
			now_showing = bms_client.get_now_showing()
			if movieName != -1:
				for movie_info in now_showing:
					if jellyfish.damerau_levenshtein_distance(movieName.lower(), movie_info[0].lower()) > 0.8:
						result.append(movie_info)
			else:
				result.append(movie_info)
		else:
			coming_soon = bms_client.get_coming_soon()
			if movieName != -1:
				for movie_info in coming_soon:
					if jellyfish.damerau_levenshtein_distance(movieName.lower(), movie_info[0].lower()) > 0.8:
						result.append(movie_info)
			else:
				result.append(movie_info)
	else:
		attributes = {
			'Intent' : 'GetMovieList'
		}
		return response_plain_text("Please provide the location", False, attributes, "No location", "Found too many results", "I'm efficient if you provide me your locatoin")


	outputSpeech = "These are the movies which are showing in your area " 
	for r in result:
		outputSpeech += r[0] + " which is showed in " + r[3] + " and the language is " + r[5]

	return response_plain_text(outputSpeech, False, {}, str(len(result)) + " movies showing", result)


def response_plain_text(output, endsession, attributes, title, cardContent, repromt):
    print(output)
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


# if __name__ == '__main__':
#   # Test code.
#   bms_client = BookMyShowClient('Bengaluru')
#   now_showing = bms_client.get_now_showing()



def getSlotValue(intent, slot):
	if 'slots' in intent:
		if slot in intent['slots']:
			return intent['slots'][slot]['value']
	
	return -1

