from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, roles, users


api_router = APIRouter()


api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    roles.router,
    prefix="/roles",
    tags=["Roles"],
)


api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)
