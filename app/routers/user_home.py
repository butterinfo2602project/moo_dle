from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status, Form
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user
        }
    )


@router.post("/app", response_class=HTMLResponse)
async def make_guess(
    request: Request,
    db: SessionDep, #doesn't need it yet
    user: AuthDep,
    d0: int = Form(),
    d1: int = Form(),
    d2: int = Form(),
    d3: int = Form()
):
    digits = [d0, d1, d2, d3]

    if len(set(digits)) != 4: #sets dont allow dupes
        return templates.TemplateResponse(
            request=request,
            name="app.html",
            context={
                "user": user,
                "error": "No duplicate digits allowed"
            }
        )

    guess = "".join(map(str, digits)) #create one number

    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "guess": guess
        }
    )