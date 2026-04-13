from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status, Form
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from app.models.game import DailyGame, UserGame, Guess
from app.models import Leaderboard
from . import router, templates
from sqlmodel import select, delete
from datetime import date as date_type, datetime, timedelta
import random

def generate_secret_number() -> str:
    digits = random.sample(range(10), 4)
    return "".join(map(str, digits))


def calculate_bulls_and_cows(guess: str, secret: str) -> tuple[int, int]:
    bulls = sum(1 for g, s in zip(guess, secret) if g == s)
    cows = sum(1 for g in guess if g in secret) - bulls
    return bulls, cows


def get_time_left():
    # counts time until tomorrow
    now = datetime.now()
    tomorrow = datetime.combine(
        date_type.today() + timedelta(days=1),
        datetime.min.time()
    )

    time_left = tomorrow - now
    total_seconds = int(time_left.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep
):
    today = date_type.today()
    
    daily_game = db.exec(select(DailyGame).where(DailyGame.game_date == today)).first()
    if not daily_game:
        daily_game = DailyGame(game_date=today, secret_number=generate_secret_number()) 
        db.add(daily_game)
        db.commit()
        db.refresh(daily_game)
    
    user_game = db.exec(
        select(UserGame).where(
            UserGame.user_id == user.id,
            UserGame.daily_game_id == daily_game.id
        )
    ).first()

    locked = False
    time_left = None

    if user_game and user_game.completed:
        locked = True
        time_left = get_time_left()
    
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user,
            "guesses": user_game.guesses if user_game else [],
            "user_game": user_game,
            "locked": locked,
            "time_left": time_left
        }
    )


@router.get("/history", response_class=HTMLResponse)
async def history_view(
    request: Request,
    user: AuthDep,
    db: SessionDep
):
    # get completed games for this user
    user_games = db.exec(
        select(UserGame).where(
            UserGame.user_id == user.id,
            UserGame.completed == True
        )
    ).all()

    history_items = []

    for game in user_games:
        daily_game = db.exec(
            select(DailyGame).where(DailyGame.id == game.daily_game_id)
        ).first()

        history_items.append({
            "date": daily_game.game_date if daily_game else None,
            "winning_code": daily_game.secret_number if daily_game else "----",
            "outcome": "Won" if game.won else "Lost",
            "attempts": game.num_attempts
        })

    # newest first
    history_items = sorted(
        history_items,
        key=lambda item: item["date"],
        reverse=True
    )

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "user": user,
            "history_items": history_items
        }
    )


@router.post("/app", response_class=HTMLResponse)
async def make_guess(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    action: str = Form("guess"),
    d0: int | None = Form(None),
    d1: int | None = Form(None),
    d2: int | None = Form(None),
    d3: int | None = Form(None)
):
    today = date_type.today()

    daily_game = db.exec(select(DailyGame).where(DailyGame.game_date == today)).first()
    if not daily_game:
        daily_game = DailyGame(game_date=today, secret_number=generate_secret_number())
        db.add(daily_game)
        db.commit()
        db.refresh(daily_game)

    user_game = db.exec(
        select(UserGame).where(
            UserGame.user_id == user.id,
            UserGame.daily_game_id == daily_game.id
        )
    ).first()

    if not user_game:
        user_game = UserGame(user_id=user.id, daily_game_id=daily_game.id)
        db.add(user_game)
        db.commit()
        db.refresh(user_game)

    if user_game.completed:
        return templates.TemplateResponse(
            request=request,
            name="app.html",
            context={
                "user": user,
                "error": "You've already completed today's game!",
                "guesses": user_game.guesses,
                "user_game": user_game,
                "locked": True,
                "time_left": get_time_left()
            }
        )

    if action == "giveup":
        user_game = handle_give_up(db, user)

        return templates.TemplateResponse(
            request=request,
            name="app.html",
            context={
                "user": user,
                "guesses": user_game.guesses,
                "user_game": user_game,
                "locked": True,
                "time_left": get_time_left(),
                "success": "You gave up!"
            }
        )

    if d0 is None or d1 is None or d2 is None or d3 is None:
        return templates.TemplateResponse(
            request=request,
            name="app.html",
            context={
                "user": user,
                "error": "Please fill in all 4 boxes",
                "guesses": user_game.guesses,
                "user_game": user_game,
                "locked": False,
                "time_left": None,
                "form_values": {
                    "d0": "" if d0 is None else d0,
                    "d1": "" if d1 is None else d1,
                    "d2": "" if d2 is None else d2,
                    "d3": "" if d3 is None else d3
                }
            }
        )

    digits = [d0, d1, d2, d3]
    
    if len(set(digits)) != 4:
        return templates.TemplateResponse(
            request=request,
            name="app.html",
            context={
                "user": user,
                "error": "No duplicate digits allowed",
                "guesses": user_game.guesses,
                "user_game": user_game,
                "form_values": {"d0": d0, "d1": d1, "d2": d2, "d3": d3},
                "locked": False,
                "time_left": None
            }
        )
    
    guess_str = "".join(map(str, digits))
    
    bulls, cows = calculate_bulls_and_cows(guess_str, daily_game.secret_number)
    
    guess = Guess(
        user_game_id=user_game.id,
        guess_number=guess_str,
        bulls=bulls,
        cows=cows
    )
    db.add(guess)
    
    user_game.num_attempts += 1
    success = None
    
    if bulls == 4:
        user_game.won = True
        user_game.completed = True
        success = f"You won! The number was {guess_str}"

        user.gamesWon += 1
        user.numGames += 1

        leaderboard = Leaderboard(
            user_id=user.id,
            game_id=daily_game.id,
            username=user.username,
            gamesWon=user.gamesWon,
            numAttempts=user_game.num_attempts
        )

        db.add(leaderboard)
        db.commit()
        db.refresh(leaderboard)

    db.commit()
    db.refresh(user_game)
    
    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "success": success,
            "guesses": user_game.guesses,
            "user_game": user_game,
            "locked": user_game.completed,
            "time_left": get_time_left() if user_game.completed else None
        }
    )


def handle_give_up(db: SessionDep, user: AuthDep):
    today = date_type.today()

    daily_game = db.exec(
        select(DailyGame).where(DailyGame.game_date == today)
    ).first()

    if not daily_game:
        raise HTTPException(status_code=404, detail="Game not found")

    user_game = db.exec(
        select(UserGame).where(
            UserGame.user_id == user.id,
            UserGame.daily_game_id == daily_game.id
        )
    ).first()

    if not user_game:
        user_game = UserGame(
            user_id=user.id,
            daily_game_id=daily_game.id,
            num_attempts=0
        )
        db.add(user_game)

    if user_game.completed:
        return user_game

    user_game.completed = True
    user_game.won = False
    user.numGames += 1

    db.add(user_game)
    db.commit()
    db.refresh(user_game)

    return user_game


@router.get("/app/nuke")
async def nuke_data(db: SessionDep, user: AuthDep):
    db.exec(delete(Guess))
    db.exec(delete(UserGame))
    db.exec(delete(DailyGame))
    db.exec(delete(Leaderboard))
    
    db.commit()
    
    return RedirectResponse(url="/app", status_code=303)