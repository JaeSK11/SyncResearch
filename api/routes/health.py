from fastapi import APIRouter
from api.dependencies import check_services

router = APIRouter()

@router.get("/")
async def health_check():
    """Check system health"""
    services = check_services()
    return {
        "status": "healthy",
        "services": services
    }