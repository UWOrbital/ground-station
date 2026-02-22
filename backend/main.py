from fastapi import FastAPI

from backend.api.backend_setup import setup_logging, setup_middlewares, setup_routes
from backend.api.lifespan import lifespan

app = FastAPI(lifespan=lifespan)
setup_logging()
setup_routes(app)
setup_middlewares(app)
