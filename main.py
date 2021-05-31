#!/usr/bin/python3
import os
from todays_events import speak_todays_events
from playsound import playsound
import speech_recognition as sr
from gtts import gTTS


def get_audio():
	r = sr.Recognizer()
	with sr.Microphone() as source:
		r.adjust_for_ambient_noise(source, duration=1)
		print("recording...")
		audio = r.listen(source)

		said = ""

		try:
			said = r.recognize_google(audio, language='es-ES')
			print(said)
		except Exception as e:
			print("Exception: " + str(e))

	return said

os.chdir("/home/manusa/Documents/programacion/calendar_assistant_python")
ans = input("Do you want to initialize the Calendar Assistant? [Y/n] ")
if ans == 'Y':
	playsound('./audio/goodmorning.mp3')
	said = get_audio()
	print('USER: "{}"'.format(said))
	if 'eventos' and 'hoy' in said:
		speak_todays_events()





exit = input("Press enter to exit...")