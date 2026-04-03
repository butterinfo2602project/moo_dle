from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import date


class GameBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    date: date
    numAttempts: int = 0
    won: bool = False
    attempted: bool = False


class Game(GameBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)