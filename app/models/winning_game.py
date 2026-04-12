from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import date


class WinningGameBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    date: date
    winning_code:int


class WinningGame(WinningGameBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)