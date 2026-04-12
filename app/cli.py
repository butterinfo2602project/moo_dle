"""
Code to create leaderboard database wiht appropriate relationships

def create_leaderboard_from_game(session, game_id: int):
    game = session.get(Game, game_id)
    user = session.get(User, game.user_id)

    leaderboard = Leaderboard(
        user_id=user.id,
        game_id=game.id,
        username=user.username,
        games_won=user.gamesWon,
        num_attempts=game.numAttempts
    )

    session.add(leaderboard)
    session.commit()
    session.refresh(leaderboard)

    return leaderboard


    This is also how to call it in the program to update the database

    if game.won:
        create_leaderboard_from_game(session, game.id)
    """