import logging

import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    logger.info("Loading environment variables")
    load_dotenv()

    logger.info("Importing API routers")
    from routers.routers import router

    logger.info("Creating FastAPI application")
    app = FastAPI()
    app.include_router(router, prefix="/api")
    logger.info("Registered API router with prefix /api")
    return app


app = create_app()

if __name__ == "__main__":
    logger.info("Starting uvicorn server on 127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
