from fastapi import FastAPI

from nas_core import __version__
from nas_core.api.routes.health import router as health_router
from nas_core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="NaS Core API",
    description="Research and evidence infrastructure for the NaS Cortex.",
    version=__version__,
)
app.include_router(health_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "name": "NaS Core API",
        "environment": settings.environment,
        "documentation": "/docs",
    }
