from fastapi import APIRouter, Request

router = APIRouter()


async def proxy(request: Request):
    """Proxies a request to a given service."""
    return "OK"
