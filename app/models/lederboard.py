from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import date


class LeaderboardBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    game_id: int = Field(foreign_key="dailygame.id")
    username: str 
    gamesWon: int
    numAttempts: int

class Leaderboard(LeaderboardBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)