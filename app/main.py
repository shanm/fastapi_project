from fastapi import FastAPI
from app.api.v1.endpoints import users

app = FastAPI(
    title="FastAPI User Management",
)

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/")
async def root():
    return {
        "message": "Application is running"
    }