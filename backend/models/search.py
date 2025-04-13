# backend/models/search.py
from typing import List, Optional
from pydantic import BaseModel

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
