#!/usr/bin/env python

import base64

from flask import Flask, redirect, request
import requests
import json

CLIENT_SECRET = '1472c5382d674be6ae04a35e83464b35'
CLIENT_ID = 'be3478ead1a24f51b2245cd13411a77f'

app = Flask(__name__)


def show_tracks(tracks):
	for i, item in enumerate(tracks['items']):
		track = item['track']
		print("   %d %32.32s %s" % (i, track['artists'][0]['name'],
									track['name']))


@app.route('/callback')
def callback():
	code = request.args.get('code')
	auth = "%s:%s" % (CLIENT_ID, CLIENT_SECRET)
	r = requests.post(url='https://accounts.spotify.com/api/token',
					  params={"grant_type": "authorization_code", "code": code,
							  "redirect_uri": "http://localhost:5000/callback"},
					  headers={'Content-Type': 'application/x-www-form-urlencoded',
							   'Authorization': 'Basic ' + base64.b64encode(
								   auth.encode()).decode()})

	# print(r.json())
	print(r.status_code)
	print(r.json())
	if r.status_code != 200:
		return 'ERREUR GETTING TOKEN'

	token = r.json()['access_token']
	return redirect('/test?token=' + token)


def clean_song(name):
	name = name.lower()
	name = name.replace('clip officiel', '')
	name = name.replace('[', '')
	name = name.replace(']', '')
	name = name.replace('(', '')
	name = name.replace(')', '')
	name = name.replace('"', '')
	name = name.replace(' - ', ' ')
	name = name.replace('_', '')
	name = name.replace(' ft. ', ' ')
	name = name.replace(' feat. ', ' ')
	name = name.replace(',', '')
	name = name.replace(' x ', ' ')

	return name


def read_songs(path='songs_to_add.txt'):
	f = open(path, 'r')
	for l in f:
		yield clean_song(l[:-1])
	f.close()


def get_spotify_id(token, name):
	r1 = requests.get(url="https://api.spotify.com/v1/search?q=%s&type=track" % name,
					  headers={
						  'Authorization': 'Bearer %s' % token}
					  )

	results = r1.json()
	if r1.status_code != 200:
		print('ERREUR GETTING SPOTIFY ID')
		return
	if len(results['tracks']['items']) == 0:
		return
	return results['tracks']['items'][0]['id']


def get_spotify_ids(token, filename):
	for track in read_songs(filename):
		id = get_spotify_id(token, track)
		if id is not None:
			print(track, id)
			yield id
		else:
			print('NOT FOUND', track)


@app.route('/add_songs')
def test():
	filename = request.args.get('filename')
	if filename is None:
		return 'PLEASE ADD ?filename=<path> TO URL'

	token = request.args.get('token')

	tracks_to_add = list(get_spotify_ids(token, filename))

	if len(tracks_to_add) == 0:
		return 'no tracks to add'

	r = requests.put(url='https://api.spotify.com/v1/me/tracks',
					 data=json.dumps({'ids': tracks_to_add}),
					 headers={
						 'Content-Type': 'application/json',
						 'Authorization': 'Bearer %s' % token})
	print(r.status_code)
	return 'ok good'


@app.route('/')
def home():
	return redirect(
		"https://accounts.spotify.com/authorize?client_id=%s&response_type=code&redirect_uri=http://localhost:5000/callback&scope=user-library-read user-library-modify" % (
			CLIENT_ID))


if __name__ == '__main__':
	app.run()
