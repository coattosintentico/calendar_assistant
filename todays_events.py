#
# Get and say today's events
#
import datetime # import all the stuff for the API to work
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import playsound # these are not from the API
from gtts import gTTS

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate_calendar():
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time. This is the function we want to run the first, to get the credentials.
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    return service

def speak(text):
	# Gets a string, transforms it to an audio file and plays it.
    print("Transforming text to speech...")
    tts = gTTS(text = text, lang = 'es-es')
    filename = 'voice.mp3'
    tts.save(filename)
    print("Transformation completed. Now playing the voice...")
    playsound.playsound(filename)
    print("Voice played succesfully.")


def transform_date_to_midnight(datetime):
    # Gets a datetime as a string in ISO format and returns it but with hour 00:00:00
    new_datetime = datetime.split('T')
    del new_datetime[1]
    new_datetime.append('00:00:00.000001Z')
    return 'T'.join(new_datetime)


# https://developers.google.com/calendar/v3/reference/events/list
def get_todays_events(service):
    # Calls the calendar API and returns the events for today as a list of dictionaries.
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    now = transform_date_to_midnight(now)
    now_date = now.split('T')[0] # Today's date as a string "YYYY-MM-DD"
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute() # get a dictionary with the events
    events = events_result.get('items', []) # extract the events perse (there are other info in that dictionary)

    # Get the events that are from today:
    todays_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date')) # Gets the datetime from each event. If not existent, that is that it's a date. 
        start_date = start.split('T')[0]
        if start_date == now_date:
            todays_events.append(event)

    return todays_events


def join_events(event_list):
    # Receives a list of events as dictionaries and returns a string with all of their summaries joined by ", " and " y ".
    events_string = ""
    for i in range(len(event_list)):
        if len(event_list) == 1:
            events_string += event_list[i]['summary']
        elif i == len(event_list)-1 != 0: # Check if it's the last one (and not the only one), because that is the special one.
            events_string += ' y ' + event_list[i]['summary']
        else:
            events_string += event_list[i]['summary'] + ', '
    return events_string


# TO IMPROVE, GET THE HOUR AND MINUTE NOT AS NUMBERS BUT AS A REAL HOUR AND FRACTION OF HOUR FORMAT
def join_social_events(event_list):
    # Receives a list of events as dictionaries and returns a string with all of their hours and summaries joined by ", " and " y ".
    events_string = ""
    for i in range(len(event_list)):
        if i == len(event_list)-1 != 0: # Check if it's the last one (and not the only one), because that is the special one.
            events_string += (', y a las ' +
                str(event_list[i]['start']['hour']) + ' ' + str(event_list[i]['start']['min']) +
                ' has quedado con ' + event_list[i]['summary'])
        elif i == 0:
            events_string += ('A las ' +
                str(event_list[i]['start']['hour']) + ' ' + str(event_list[i]['start']['min']) +
                ' has quedado con ' + event_list[i]['summary'])
        else:
            events_string += (', a las ' +
                str(event_list[i]['start']['hour']) + ' ' + str(event_list[i]['start']['min']) +
                ' has quedado con ' + event_list[i]['summary'])            
    return events_string


def speak_todays_events():
	#
	#   Main function:
	#
	print("Getting keys to calendar...")
	service = authenticate_calendar() # get the credentials in service to know what google user get the info from
	print("Accessed succesfully.")
	print("Getting info from the calendar...")
	todays_events = get_todays_events(service)
	print("Info obtained succesfully.")

	# Working events are going to be divided in morning & evening.
	# Social events don't; they're going to be classified (and announced) by hour.
	morning_events = []
	evening_events = []
	social_events  = []
	print("Organizing events info...")
	for event in todays_events:
	    start_time = {
	        'hour': int(event['start'].get('dateTime').split('T')[1].split('+')[0][:2]),
	        'min': int(event['start'].get('dateTime').split('T')[1].split('+')[0][3:5])}
	    if event.get('colorId') == '4':
	        social_events.append({'summary': event['summary'], 'start': start_time}) # Check if social and add it.
	    else: # If not, get the starting hour and classify it in morning or evening.
	        if int(start_time['hour']) <= 15:
	            morning_events.append({'summary': event['summary']})
	        else:
	            evening_events.append({'summary': event['summary']})
	# Now we have the events classified in morning, evening and social.

	goodmorning_text = "Hoy tienes {:d} eventos en tu agenda. ".format(len(todays_events))

	if not morning_events: # Check if there are no morning events.
	    morning_text = "Por la mañana no tienes eventos. "
	else:
	    morning_text = "Por la mañana tienes que " + join_events(morning_events) + ". "
	if not evening_events: # Repeat with the evening events.
	    evening_text = "Por la tarde no tienes eventos. "
	else:
	    evening_text = "Por la tarde tienes que " + join_events(evening_events) + ". "
	if not social_events:
	    social_text = "Hoy no hay eventos de índole social y o amistosa. "
	else:
	    social_text = "De índole social y o amistosa, " + join_social_events(social_events) + ". "

	bye_text = "Eso es todo por hoy. Un saludito y suerte con el día."

	text = goodmorning_text + morning_text + evening_text + social_text + bye_text
	print("Info organized succesfully.")
	speak(text)


if __name__ == '__main__':
	speak_todays_events()