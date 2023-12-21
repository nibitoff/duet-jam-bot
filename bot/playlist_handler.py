import csv
import os
import spotipy
import random
import re
from logs import logged_execution

from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

@logged_execution
def get_generated_playlist(playlist, playlist_link_1, playlist_link_2):
    playlist_1 = list()
    playlist_2 = list()
    generated_playlist = list()
    client_credentials_manager = SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )
    # create spotify session object
    session = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    # get uri from https link
    if match := re.match(r"https://open.spotify.com/playlist/(.*)\?", playlist_link_1):
        playlist_uri = match.groups()[0]
    else:
        raise ValueError("Expected format: https://open.spotify.com/playlist/...")

    # get list of tracks in a given playlist (note: max playlist length 100)
    tracks = session.playlist_tracks(playlist_uri)["items"]
    for track in tracks:
        name = track["track"]["name"]
        artists = ", ".join(
            [artist["name"] for artist in track["track"]["artists"]]
        )
        song = [name, artists]
        playlist_1.append(song)

    if match := re.match(r"https://open.spotify.com/playlist/(.*)\?", playlist_link_2):
        playlist_uri = match.groups()[0]
    else:
        raise ValueError("Expected format: https://open.spotify.com/playlist/...")

    # get list of tracks in a given playlist (note: max playlist length 100)
    tracks = session.playlist_tracks(playlist_uri)["items"]
    for track in tracks:
        name = track["track"]["name"]
        artists = ", ".join(
            [artist["name"] for artist in track["track"]["artists"]]
        )
        song = [name, artists]
        playlist_2.append(song)

    generated_playlist = playlist_1 + playlist_2
    random.shuffle(generated_playlist)

    csv_writer = csv.writer(playlist, quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["track", "artist"])
    csv_writer.writerows(generated_playlist)

