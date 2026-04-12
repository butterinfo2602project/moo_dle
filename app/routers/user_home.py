from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status, Form
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from app.models.game import DailyGame, UserGame, Guess
from . import router, templates
from sqlmodel import select, delete
from datetime import date as date_type
import random

"""Todo List:
        still needs to implement the actual game model for history
        hide the inputs when the game has been finished for the day(maybe a countdown)
        remove delete data button
        dont use session, it's not restful
        gotta change it so that when other chars are entered, the history still shows
        make it so that when you refresh it doesn't re-enter it
"""

def generate_secret_number() -> str:
    digits = random.sample(range(10), 4)
    return "".join(map(str, digits))


def calculate_bulls_and_cows(guess: str, secret: str) -> tuple[int, int]:
    bulls = sum(1 for g, s in zip(guess, secret) if g == s)
    cows = sum(1 for g in guess if g in secret) - bulls
    return bulls, cows


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
    
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user,
            "guesses": user_game.guesses if user_game else [],
            "user_game": user_game
        }
    )


@router.post("/app", response_class=HTMLResponse)
async def make_guess(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    d0: int = Form(),
    d1: int = Form(),
    d2: int = Form(),
    d3: int = Form()
):
    try:
        digits = [d0, d1, d2, d3]
    except ValueError:
        return templates.TemplateResponse(
            request=request,
            name="app.html",
            context={
                "user": user,
                "error": "Please enter numbers only"
            }
        )
    
    if len(set(digits)) != 4:
        today = date_type.today()
        daily_game = db.exec(select(DailyGame).where(DailyGame.game_date == today)).first()
        user_game = None
        guesses = []
        
        if daily_game:
            user_game = db.exec(
                select(UserGame).where(UserGame.user_id == user.id,
                    UserGame.daily_game_id == daily_game.id)).first()

            if user_game:
                guesses = user_game.guesses
        
        return templates.TemplateResponse(
            request=request,
            name="app.html",
            context={
                "user": user,
                "error": "No duplicate digits allowed",
                "guesses": guesses,
                "user_game": user_game,
                "form_values": {"d0": d0, "d1": d1, "d2": d2, "d3": d3}
            }
        )
    
    guess_str = "".join(map(str, digits))
    
    today = date_type.today()
    
    # get or create today's game
    daily_game = db.exec(select(DailyGame).where(DailyGame.game_date == today)).first()
    if not daily_game:
        daily_game = DailyGame(game_date=today, secret_number=generate_secret_number())
        db.add(daily_game)
        db.commit()
        db.refresh(daily_game)
    
    
    user_game = db.exec(
        select(UserGame).where(UserGame.user_id == user.id,
        UserGame.daily_game_id == daily_game.id )).first()# doesn't allow user to match to previous days
    
    if not user_game:
        user_game = UserGame(user_id=user.id, daily_game_id=daily_game.id)
        db.add(user_game)
        db.commit()
        db.refresh(user_game)
    
    # check today's game status (hide if completed)
    if user_game.completed:
        return templates.TemplateResponse(
            request=request,
            name="app.html",
            context={
                "user": user,
                "error": "You've already completed today's game!",
                "guesses": user_game.guesses,
                "user_game": user_game
            }
        )
    
    # number placement
    bulls, cows = calculate_bulls_and_cows(guess_str, daily_game.secret_number)
    
    # create guess
    guess = Guess(
        user_game_id=user_game.id,
        guess_number=guess_str,
        bulls=bulls,
        cows=cows
    )
    db.add(guess)
    
    user_game.num_attempts += 1
    success = f"You entered: {guess_str} - Bulls: {bulls}, Cows: {cows}"
    
    if bulls == 4:
        user_game.won = True
        user_game.completed = True
        success = f"You won! The number was {guess_str}"
    
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
        }
    )




@router.get("/app/nuke")
async def nuke_data(db: SessionDep, user: AuthDep):
    

    #just so I can test things
    db.exec(delete(Guess))
    db.exec(delete(UserGame))
    db.exec(delete(DailyGame))
    
    db.commit()
    
    return RedirectResponse(url="/app", status_code=303)