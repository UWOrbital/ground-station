from fastapi import FastAPI

from app.api.backend_setup import setup_logging, setup_middlewares, setup_routes
from app.api.lifespan import lifespan
from app.exceptions.exception_handlers import setup_exception_handlers

app = FastAPI(lifespan=lifespan)
setup_logging()
setup_routes(app)
setup_middlewares(app)
setup_exception_handlers(app)
