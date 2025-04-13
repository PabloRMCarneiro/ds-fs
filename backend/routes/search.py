# backend/routes/search.py
import concurrent.futures
from fastapi import APIRouter, HTTPException
from models.search import SearchPayload, SearchResponse, SpotifyInfo, TrackInfo
from utils.youtube import get_youtube_results
from core.spotify_client import spotify_client as sp

router = APIRouter()

def is_valid_spotify_playlist(url: str) -> bool:
    import re
    pattern = r'https?://open\.spotify\.com/playlist/[\w\d]+'
    return re.match(pattern, url) is not None

@router.post("/search", response_model=SearchResponse)
async def search_playlist(payload: SearchPayload):
    playlist_url = payload.url
    if not is_valid_spotify_playlist(playlist_url):
        raise HTTPException(status_code=400, detail="URL inválida. Por favor, insira uma URL válida do Spotify.")

    try:
        playlist_data = sp.playlist(playlist_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar a playlist: {str(e)}")

    playlist_name = playlist_data.get("name", "Playlist")
    tracks_data = playlist_data.get("tracks", {})
    tracks_items = tracks_data.get("items", [])

    def process_track(item):
        track = item.get("track")
        if not track:
            return None
        # Constrói a informação de Spotify
        spotify_info = SpotifyInfo(
            title=track.get("name"),
            artists=", ".join(artist.get("name") for artist in track.get("artists", [])),
            id=track.get("id")
        )
        search_title = f"{spotify_info.title} - {spotify_info.artists}"
        youtube_results = get_youtube_results(search_title)
        return TrackInfo(spotify=spotify_info, youtube=youtube_results)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        processed_tracks = list(executor.map(process_track, tracks_items))
    tracks_response = [track for track in processed_tracks if track is not None]

    return SearchResponse(playlist_name=playlist_name, tracks=tracks_response)
