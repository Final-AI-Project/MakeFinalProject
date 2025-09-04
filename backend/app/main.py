from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, users, plants


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(plants.router, prefix="/api/v1")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/version")
async def version():
    return {"version": "0.1.0"}
