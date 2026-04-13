import uvicorn
from fastapi import FastAPI, Request, status
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from app.routers import templates, static_files, router, api_router
from app.config import get_settings
from contextlib import asynccontextmanager
from app.database import create_db_and_tables, get_cli_session
from app.database import Session, engine
from app.repositories.user import UserRepository
from app.services.auth_service import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    with Session(engine) as db:
        user_repo = UserRepository(db)
        auth_service = AuthService(user_repo)

        try:
            auth_service.register_user(
                username="bob",
                email="bob@mail.com",
                password="bobpass"
            )
        except Exception:
            print("(ignored)")

    yield


app = FastAPI(middleware=[
    Middleware(SessionMiddleware, secret_key=get_settings().secret_key)
],
    lifespan=lifespan
)   

app.include_router(router)
app.include_router(api_router)
app.mount("/static", static_files, name="static")

@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_redirect_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        request=request, 
        name="401.html",
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=get_settings().app_host, port=get_settings().app_port, reload=get_settings().env.lower()!="production")