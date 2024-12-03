from fastapi import APIRouter

from apps.dash.urls import dashRouter

router = APIRouter()

router.include_router(dashRouter, prefix='/dash')
