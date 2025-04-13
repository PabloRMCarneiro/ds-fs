# backend/models/download.py
from typing import List
from pydantic import BaseModel

class DownloadTrack(BaseModel):
    spotify_id: str
    url: str

class DownloadPayload(BaseModel):
    playlist_name: str
    tracks: List[DownloadTrack]
