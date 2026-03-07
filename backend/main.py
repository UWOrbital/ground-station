from api.backend_setup import setup_logging, setup_middlewares, setup_routes
from api.lifespan import lifespan
from fastapi import FastAPI

app = FastAPI(lifespan=lifespan)
setup_logging()
setup_routes(app)
setup_middlewares(app)
