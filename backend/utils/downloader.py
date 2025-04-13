# backend/utils/downloader.py
import subprocess

def download_by_link(link_song: str, id_song: str, download_dir: str):
    """
    Executa o comando ytmdl para baixar a música do YouTube.
    """
    if not link_song:
        print("Nenhum link encontrado para download.")
        return
    try:
        command = f'ytmdl --url "{link_song}" --quiet -o "{download_dir}" --spotify-id "{id_song}"'
        subprocess.call(command, shell=True)
    except Exception as e:
        print(f"Erro ao baixar a música: {e}")
