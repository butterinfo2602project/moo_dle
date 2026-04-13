from sqlmodel import Session, select
from app.models import Leaderboard, UserGame, User, DailyGame


def create_leaderboard_from_game(session: Session, user_game_id: int):
    user_game = session.get(UserGame, user_game_id)
    if not user_game:
        return None

    user = session.get(User, user_game.user_id)
    daily_game = session.get(DailyGame, user_game.daily_game_id)

    if not user or not daily_game:
        return None

    # prevent duplicates for same user/day
    existing = session.exec(
        select(Leaderboard).where(
            Leaderboard.user_id == user.id,
            Leaderboard.game_id == daily_game.id
        )
    ).first()

    if existing:
        return existing

    leaderboard = Leaderboard(
        user_id=user.id,
        game_id=daily_game.id,
        username=user.username,
        games_won=user.gamesWon,
        num_attempts=user_game.num_attempts
    )

    session.add(leaderboard)
    session.commit()
    session.refresh(leaderboard)

    return leaderboard