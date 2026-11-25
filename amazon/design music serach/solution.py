from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

class State(Enum):
    IDLE = 1
    PLAYING = 2
    PAUSED = 3

@dataclass
class Song:
    id: int
    name: str
    artist: str
    album_id: str

class CatalogSearch:
    def search(self, keyword: str) -> List[Song]:
        pass

@dataclass
class PlaylistEntry:
    id: int
    song_id: int

class Playlist:
    def __init__(self, id: int, owner: str, catalog_search: CatalogSearch):
        self.id = id
        self.owner = owner
        self.entries: List[PlaylistEntry] = []
        self.songs: List[Song] = []
        self.catalog_search = catalog_search

    def add(self, song: Song) -> bool:
        pass

    def remove(self, entry: PlaylistEntry) -> bool:
        pass

    def reorder(self, new_order: any):
        pass

    def search(self, keyword: str) -> List[Song]:
        if keyword == "":
            raise Exception("keyword must not be empty")
        return self.catalog_search.search(keyword)

class PlaybackSession:
    def __init__(self, songs: List[Song], entries: List[PlaylistEntry]):
        self.songs = songs
        self.entries = entries
        self.state = State.IDLE
        self.index: Optional[int] = None
        self.loaded_song_id: Optional[int] = None
        self.current_position = 0

    def reset(self):
        if self.loaded_song_id is None:
            raise ValueError("No song is loaded")
        self.current_position = 0
        self.state = State.PAUSED

    def play(self, entry_index: int):
        if not 0 <= entry_index < len(self.entries):
            raise IndexError("Invalid playlist entry index")
        song_id = self.entries[entry_index].song_id
        if not any(song.id == song_id for song in self.songs):
            raise ValueError(f"Unknown song ID: {song_id}")

        if song_id != self.loaded_song_id:
            self.current_position = 0
        self.loaded_song_id = song_id
        self.index = entry_index
        self.state = State.PLAYING

    def pause(self):
        if self.loaded_song_id is None:
            raise ValueError("No song is loaded")
        self.state = State.PAUSED