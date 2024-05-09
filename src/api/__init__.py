from fastapi import APIRouter

from .monitoring.views import router as monitoring

router = APIRouter()
router.include_router(monitoring, prefix="/monitoring", tags=["monitoring"])
