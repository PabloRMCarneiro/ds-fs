# backend/core/spotify_client.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from .config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID, 
    client_secret=SPOTIFY_CLIENT_SECRET
)
spotify_client = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
