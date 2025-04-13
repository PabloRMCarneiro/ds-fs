# backend/routes/download.py
import os
import shutil
import tempfile
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from models.download import DownloadPayload
from utils.downloader import download_by_link
from utils.zip_utils import zip_directory

router = APIRouter()

@router.post("/download")
async def download_playlist(payload: DownloadPayload, background_tasks: BackgroundTasks):
    playlist_name = payload.playlist_name
    tracks = payload.tracks

    # Cria diretório temporário
    temp_download_dir = tempfile.mkdtemp(prefix="downloads_")
    download_dir = os.path.join(temp_download_dir, playlist_name)
    os.makedirs(download_dir, exist_ok=True)

    # Faz download de cada música
    for track in tracks:
        download_by_link(track.url, track.spotify_id, download_dir)

    # Compacta os arquivos
    zip_filename = f"{playlist_name}.zip"
    zip_filepath = os.path.join(temp_download_dir, zip_filename)
    zip_directory(download_dir, zip_filepath)

    # Agenda a limpeza dos arquivos temporários
    def cleanup_temp_files(path: str):
        shutil.rmtree(path, ignore_errors=True)

    background_tasks.add_task(cleanup_temp_files, temp_download_dir)
    return FileResponse(zip_filepath, media_type="application/zip", filename=zip_filename)
