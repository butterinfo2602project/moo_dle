from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime, date as date_type

# this could be used to save history
class DailyGame(SQLModel, table=True): #for secret number
    id: Optional[int] = Field(default=None, primary_key=True)
    game_date: date_type = Field(default_factory=date_type.today, unique=True, index=True)  # only once per day
    secret_number: str = Field(max_length=4)
    
    user_attempts: List["UserGame"] = Relationship(back_populates="daily_game")


class UserGame(SQLModel, table=True): # user's attempts
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    daily_game_id: int = Field(foreign_key="dailygame.id")
    num_attempts: int = 0
    won: bool = False
    completed: bool = False
    last_played: datetime = Field(default_factory=datetime.utcnow)
    
    
    daily_game: DailyGame = Relationship(back_populates="user_attempts")
    guesses: List["Guess"] = Relationship(back_populates="user_game")


class Guess(SQLModel, table=True): # user's guesses
    id: Optional[int] = Field(default=None, primary_key=True)
    user_game_id: int = Field(foreign_key="usergame.id")
    guess_number: str = Field(max_length=4)
    bulls: int = 0
    cows: int = 0
    
    
    user_game: UserGame = Relationship(back_populates="guesses")