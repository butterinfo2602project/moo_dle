from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import date


class GameBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    date: date
    numAttempts: int = 0
    won: bool = False
    attempted: bool = False
    guess : int #updated in db evenytime a new guess is made, this is compaired to winning_code in winnign_game db to seee if won
                #if not won then bulls and cows are updated

                
    bulls: int #updated in db evenytime a new guess is made
    cows: int #updated in db evenytime a new guess is made


class Game(GameBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)