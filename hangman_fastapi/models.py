from pydantic import BaseModel
from typing import List, Optional

class PlayerCreate(BaseModel):
    name: str

class PlayerResponse(BaseModel):
    player_id: int
    name: str

class GameStart(BaseModel):
    player_id: int
    word: Optional[str] = None  # Opcional: pode fornecer uma palavra específica

class GuessRequest(BaseModel):
    game_id: int
    letter: str

class GameResponse(BaseModel):
    game_id: int
    masked_word: str
    attempts_left: int
    hit: Optional[bool] = None
    status: str
    tried_letters: List[str]

class ScoreboardEntry(BaseModel):
    player_name: str
    games_played: int
    games_won: int
    win_rate: float