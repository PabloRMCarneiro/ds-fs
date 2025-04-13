import re
import os
import subprocess
import zipfile
import shutil
import tempfile
import concurrent.futures
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from pydantic import BaseModel
from typing import List, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch

app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# ----------------------- CONFIGURAÇÃO DO SPOTIFY -----------------------
CLIENT_ID = "a506ea84250e4abfa825f4297e73af0c"  # Substitua pelo seu Client ID
CLIENT_SECRET = "f457070b3dca4fbf805e54a5ac521c31"  # Substitua pelo seu Client Secret
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# ----------------------- MODELS -----------------------
class SearchPayload(BaseModel):
    url: str

class SpotifyInfo(BaseModel):
    title: str
    artists: str
    id: str

class YoutubeInfo(BaseModel):
    thumbnail: Optional[str]
    title: Optional[str]
    channel: Optional[str]
    duration: Optional[str]
    views: Optional[int]
    url: Optional[str]

class TrackInfo(BaseModel):
    spotify: SpotifyInfo
    youtube: List[YoutubeInfo]

class SearchResponse(BaseModel):
    playlist_name: str
    tracks: List[TrackInfo]

class DownloadTrack(BaseModel):
    spotify_id: str
    url: str

class DownloadPayload(BaseModel):
    playlist_name: str
    tracks: List[DownloadTrack]
# -------------------------------------------------------

# ----------------------- FUNÇÕES AUXILIARES -----------------------
def is_valid_spotify_playlist(url: str) -> bool:
    """
    Valida se a URL é do formato de uma playlist do Spotify.
    """
    pattern = r'https?://open\.spotify\.com/playlist/[\w\d]+'
    return re.match(pattern, url) is not None

def parse_views(views_str: str) -> int:
    """
    Converte uma string de visualizações como "5.597 visualizações"
    para um valor inteiro (ex: 5597).
    """
    try:
        numeric_part = views_str.split(" ")[0]
        clean_number = ''.join(ch for ch in numeric_part if ch.isdigit())
        return int(clean_number) if clean_number else 0
    except Exception as e:
        print(f"Erro ao converter views '{views_str}': {e}")
        return 0

def get_youtube_results(search_song_title: str) -> List[YoutubeInfo]:
    """
    Realiza a busca no YouTube e retorna uma lista de resultados formatados.
    Cada resultado contém thumbnail, title, channel, duration, views (como inteiro) e url completa.
    """
    try:
        results = YoutubeSearch(search_song_title, max_results=5).to_dict()
        youtube_results = []
        for res in results:
            thumbnail = None
            if "thumbnails" in res:
                if isinstance(res["thumbnails"], list) and len(res["thumbnails"]) > 0:
                    thumbnail = res["thumbnails"][0]
                else:
                    thumbnail = res["thumbnails"]

            raw_views = res.get("views", "0")
            views_int = parse_views(raw_views)

            youtube_results.append(YoutubeInfo(
                thumbnail=thumbnail,
                title=res.get("title"),
                channel=res.get("channel"),
                duration=res.get("duration"),
                views=views_int,
                url='https://www.youtube.com' + res.get("url_suffix", "")
            ))
        return youtube_results
    except Exception as e:
        print(f"Erro durante a busca no YouTube para '{search_song_title}': {e}")
        return []

def download_by_link(link_song: str, id_song: str, download_dir: str):
    """
    Executa o comando ytmdl para baixar a música do YouTube utilizando o link e o ID do Spotify.
    """
    if not link_song:
        print("Nenhum link encontrado para download.")
        return
    try:
        command = f'ytmdl --url "{link_song}" --quiet -o "{download_dir}" --spotify-id "{id_song}"'
        subprocess.call(command, shell=True)
    except Exception as e:
        print(f"Erro ao baixar a música: {e}")

def zip_directory(dir_path: str, zip_path: str):
    """
    Compacta o diretório informado em um arquivo ZIP.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dir_path)
                zipf.write(file_path, arcname)
# -------------------------------------------------------

# ----------------------- ENDPOINTS -----------------------
@app.post("/search", response_model=SearchResponse)
async def search_playlist(payload: SearchPayload):
    """
    Endpoint para a pesquisa inicial da playlist:
      - Valida se a URL é uma playlist do Spotify.
      - Busca os metadados da playlist e de cada faixa.
      - Para cada música, realiza a busca no YouTube em paralelo retornando 5 resultados.
    """
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

@app.post("/download")
async def download_playlist(payload: DownloadPayload, background_tasks: BackgroundTasks):
    """
    Endpoint para o download de todas as músicas:
      - Recebe o nome da playlist e os tracks com o id do Spotify e a URL do vídeo escolhido.
      - Cria um diretório temporário exclusivo para os downloads.
      - Para cada track, executa o comando para download utilizando o ytmdl.
      - Compacta o diretório em um arquivo ZIP.
      - Retorna o arquivo ZIP para o usuário e agenda a remoção do diretório temporário.
    """
    playlist_name = payload.playlist_name
    tracks = payload.tracks

    # Cria um diretório temporário único para o download
    temp_download_dir = tempfile.mkdtemp(prefix="downloads_")
    download_dir = os.path.join(temp_download_dir, playlist_name)
    os.makedirs(download_dir, exist_ok=True)

    # Efetua o download de cada música
    for track in tracks:
        download_by_link(track.url, track.spotify_id, download_dir)

    # Cria o arquivo ZIP no mesmo diretório temporário
    zip_filename = f"{playlist_name}.zip"
    zip_filepath = os.path.join(temp_download_dir, zip_filename)
    zip_directory(download_dir, zip_filepath)

    # Função para remover o diretório temporário após enviar o arquivo
    def cleanup_temp_files(path: str):
        shutil.rmtree(path, ignore_errors=True)

    # Agenda a limpeza do diretório temporário
    background_tasks.add_task(cleanup_temp_files, temp_download_dir)

    return FileResponse(zip_filepath, media_type="application/zip", filename=zip_filename)

# ----------------------- EXECUÇÃO -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
