# Alexa - Flick
> *Movies at your finger tip*

This skill let you know about the movies which are showing right now in your city as well as the movies which are about to show in your city.
The user is asked for the city, hence the user may request for movies showing in any city in India.

##### Features
- Tells the movies showing right now
- Tells the movies coming soon


A little info about Alexa - Slots
(I edited a [wiki tag on stackoverflow][7], thought it would be better to post the same here.)

A container used by Alexa, capable of holding useful piece of information provided by user like Date, Time, City, Country, Fictional Character, Author, Movies, etc. 


Source : https://developer.amazon.com/docs/custom-skills/slot-type-reference.html#list-slot-types 

Alexa Skills kit supports **slot**, which are basically containers which are helpful in obtaining specific data which the user has provided in any format to the skill. This input data is useful for the developer to return the necessary response with regards to the input data.  

**For example** : Consider you're making a skill which tells you the day of a particular date. More precisely, you give it a date and it returns you the day of the week.

Slots would be useful to obtain the input data `Date` which the user has specified, and using some logic day of the week can be figured out.

Consider this conversation:
Alexa: "Welcome to the days of our life". // "days of our life" is the invokation name of this hypothetical skill.
User: "What was the day on {1st May, 1996}" // {1st May, 1996} is the value recieved by slot `{Date}`
Alexa: "It was a Wednesday".


### Slots Type
The Alexa Skills Kit supports several slot types that define how data in the slot is recognized and handled. There are built-in slots type ([list of slot types][1]), as well as the developer can specify their own custom slot type. When creating their custom slots they are required to give some *slot values*, in the Alexa skill builder's build section. When the Alexa skill comes across such values, it would know these are the slot values of the custom build slot.

Since the skill can be published in several languages (see [languages supported by Alexa][2]), the build-in slot are also supported in several languages.


### Defining slots
Slots may be defined in the *Build* section of new Alexa skill builder or using the JSON Editor to edit the Intent Schema.

This is how the slots `Query` and `CityList` is defined in the intent schema.
~~~~
{
  "intents": [
    {
      "name": "SearchIntent",
      "slots": [
        {
          "name": "Query",
          "type": "AMAZON.SearchQuery"
        },
        {
          "name": "CityList",
          "type": "AMAZON.US_CITY"
        }
      ],
      "samples": [
        "search for {Query} near me",
        "find out {Query}",
        "search for {Query}",
        "give me details about {CityList}"
      ]
    }
  ]
}
~~~~

### Synonyms for slot values
The slot values defined in Alexa skill builder can have synonyms too. For example if you're working with a skill which asks for the *city* in which the user lives in, then places like Mumbai and Banglore could have synonyms Bombay and Bengaluru, respectively. 

 [![Custom Slot Example][3]][3]  


### Slot Filling
For filling slots there are two cases which the developer must understand.

 1. Slot value is always required.
 2. Slot value is only sometimes required, i.e. the skill will still work if this slot is missing.

If the slot value is always required, then the [directive `Dialog.Delegate`][5] may be used. To use this directive, **prompts** which the Alexa will say to ask for this slot and **utterances** that the user will speak in response to those prompts should be defined in the Alexa skill builder.

Like these :
Here the prompts and utterances are given for the custom slot `CITY` which is required by Intent `GetMoviesNowShowing`. 

[![Prompts and Utterances for custom slot - CITY][4]][4] 

And if the slot is not always required, then the [Directive `Dialog.ElicitSlot`][6] may be used. For this directive no prompts and utterances are required, the developer has to provide explicit `outputSpeech`, which is used by Alexa as a prompt for the slot filling.


### Accessing slot values
The slot values may be accessed in the lambda function. When an intent is invoked, a JSON input is given to the lambda function. Developer can access this JSON input to retrieve the slot value input given by the user. It looks something like this: 
~~~~
"intent": {
	"name": "GetAntonymsIntent",
	"confirmationStatus": "NONE",
	"slots": {
		"LANGUAGE": {
			"name": "LANGUAGE",
			"confirmationStatus": "NONE",
			"value" : "english"
		},
		"WORD": {
			"name": "WORD",
			"value": "ace",
			"resolutions": {
				"resolutionsPerAuthority": [
					{
						"authority": "amzn1.er-authority.echo-sdk.amzn1.ask.skill.c4a5d570-8455-4496-825b-07864b4acfec.WORD",
						"status": {
							"code": "ER_SUCCESS_MATCH"
						},
						"values": [
							{
								"value": {
									"name": "ace",
									"id": "360e2ece07507675dced80ba867d6dcd"
								}
							}
						]
					}
				]
			},
			"confirmationStatus": "NONE"
		}
	}
}
~~~~
Here the slots `LANGUAGE` and `WORD` have values "english" and "ace", respectively.

There can be as many slots as the developer desire, but having a lot of them increases the complexity of the skill.




  [1]: https://developer.amazon.com/docs/custom-skills/slot-type-reference.html#list-slot-types
  [2]: https://aws.amazon.com/blogs/aws/polly-text-to-speech-in-47-voices-and-24-languages/
  [3]: https://i.stack.imgur.com/UIo2p.png
  [4]: https://i.stack.imgur.com/OV9ua.png
  [5]: https://developer.amazon.com/docs/custom-skills/dialog-interface-reference.html#delegate
  [6]: https://developer.amazon.com/docs/custom-skills/dialog-interface-reference.html#elicitslot
  [7]: https://stackoverflow.com/tags/alexa-slot/info 