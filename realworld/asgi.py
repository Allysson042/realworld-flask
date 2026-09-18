from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from realworld.api.routes.v1.articles.router import router as articles_router
from realworld.api.routes.v1.profiles.router import router as profiles_router
from realworld.api.routes.v1.tags.router import router as tags_router
from realworld.api.routes.v1.users.router import router as users_router

app = FastAPI()

# CORS support (FastAPI counterpart of the former flask-cors extension).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/ping", response_class=PlainTextResponse)
def ping():
    return "pong"


app.include_router(articles_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(profiles_router, prefix="/api/profiles")
app.include_router(tags_router, prefix="/api/tags")
