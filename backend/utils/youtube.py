# backend/utils/youtube.py
import re
from typing import List
from . import downloader  # se precisar chamar funções que também estão em outros módulos
from models.search import YoutubeInfo

def parse_views(views_str: str) -> int:
    """Converte uma string de visualizações para inteiro."""
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
    """
    from youtube_search import YoutubeSearch  # import local para isolar possíveis falhas
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
