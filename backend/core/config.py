# backend/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # carrega o arquivo .env

# Configurações do Spotify lidas do .env
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise Exception("As credenciais do Spotify não foram configuradas corretamente no .env.")
