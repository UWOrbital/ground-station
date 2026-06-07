from api.backend_setup import setup_logging, setup_middlewares, setup_routes
from api.lifespan import lifespan
from exceptions.exception_handlers import setup_exception_handlers
from fastapi import FastAPI

app = FastAPI(lifespan=lifespan)
setup_logging()
setup_routes(app)
setup_middlewares(app)
setup_exception_handlers(app)
