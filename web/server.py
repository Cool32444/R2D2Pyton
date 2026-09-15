from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext

import sys
import os

# Allow importing R2D2.py from the parent directory
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

import R2D2


app = FastAPI(title="R2D2 AI")


# ============================================================
# PASSWORD CONFIGURATION
# ============================================================

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

PASSWORD_HASH = os.environ.get("R2D2_PASSWORD_HASH")

if not PASSWORD_HASH:
    raise RuntimeError(
        "R2D2_PASSWORD_HASH environment variable is not set."
    )


# ============================================================
# SESSION CONFIGURATION
# ============================================================

SESSION_SECRET = os.environ.get("R2D2_SESSION_SECRET")

if not SESSION_SECRET:
    raise RuntimeError(
        "R2D2_SESSION_SECRET environment variable is not set."
    )


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=60 * 60 * 24 * 7,  # 7 days
    same_site="lax",
    https_only=True
)


# ============================================================
# AUTHENTICATION
# ============================================================

def is_authenticated(request: Request):
    return request.session.get("authenticated") is True


# ============================================================
# LOGIN
# ============================================================

@app.get("/login")
async def login_page():
    return RedirectResponse("/static/login.html")


@app.post("/login")
async def login(
    request: Request,
    password: str = Form(...)
):

    if pwd_context.verify(password, PASSWORD_HASH):

        request.session["authenticated"] = True

        return RedirectResponse(
            "/",
            status_code=303
        )

    return RedirectResponse(
        "/login.html?error=1",
        status_code=303
    )


# ============================================================
# LOGOUT
# ============================================================

@app.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        "/login.html",
        status_code=303
    )


# ============================================================
# CHAT API
# ============================================================

@app.post("/api/chat")
async def chat(
    request: Request
):

    if not is_authenticated(request):
        return {
            "error": "Not authenticated"
        }

    data = await request.json()

    message = data.get("message", "").strip()

    if not message:
        return {
            "error": "Message is empty"
        }

    response = R2D2.sendToGemini(message)

    return {
        "response": response
    }


# ============================================================
# WEBSITE
# ============================================================

@app.get("/")
async def home(request: Request):

    if not is_authenticated(request):
        return RedirectResponse("/static/login.html")

    from fastapi.responses import FileResponse

    return FileResponse(
        "web/static/index.html"
    )


app.mount(
    "/static",
    StaticFiles(directory="web/static"),
    name="static"
)