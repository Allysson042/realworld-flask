from fastapi import FastAPI, HTTPException

from realworld.api.routes.v1.articles.router import router as articles_router
from realworld.api.routes.v1.profiles.router import router as profiles_router
from realworld.api.routes.v1.tags.router import router as tags_router
from realworld.api.routes.v1.users.router import router as users_router

app = FastAPI()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/ping")
def ping():
    raise HTTPException(status_code=501)


app.include_router(articles_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(profiles_router, prefix="/api/profiles")
app.include_router(tags_router, prefix="/api/tags")
