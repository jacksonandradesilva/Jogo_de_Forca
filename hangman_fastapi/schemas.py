from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class GameBase(BaseModel):
    word: str
    current_state: str
    guessed_letters: str
    attempts_left: int
    max_attempts: int
    status: str

class GameCreate(BaseModel):
    difficulty: Optional[str] = "medium"

class GameResponse(GameBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class GuessLetter(BaseModel):
    letter: str

class WordBase(BaseModel):
    word: str
    category: str
    difficulty: str

class WordCreate(WordBase):
    pass

class WordResponse(WordBase):
    id: int
    
    class Config:
        from_attributes = True