import uvicorn
import subprocess
from fastapi import FastAPI, Depends
from routes.home import home_route, auth_route
from routes.admin import admin_route

from database.database import init_db, get_session
from fastapi.middleware.cors import CORSMiddleware
from services.logging.logging import get_logger
from services.service.mlmodelService import BaseMLModel
from services.service.build_prompt_enhancer_model import build_prompt_enhancer_model
from services.service.UnitOfWork import UnitOfWork
from sqlmodel import Session

logging = get_logger(logger_name=__name__)

# Глобальная переменная модели
_ml_model: BaseMLModel = None


def get_ml_model() -> BaseMLModel:
    if _ml_model is None:
        raise RuntimeError("ML-модель не инициализирована")
    return _ml_model


def create_app() -> FastAPI:
    global _ml_model

    app = FastAPI()

    origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_db()
    subprocess.run(["dvc", "pull"])
    logging.info("dvc pull")

    # Инициализация модели
    _ml_model = build_prompt_enhancer_model()
    logging.info("PromptEnhancerModel initialized")

    # Передача зависимости
    app.include_router(home_route)
    app.include_router(auth_route)
    app.include_router(admin_route)

    return app


app = create_app()

if __name__ == "__main__":
    logging.info("api run")
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
