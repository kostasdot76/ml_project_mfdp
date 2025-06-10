import uvicorn
import subprocess
from fastapi import FastAPI, Depends
from routes.home import home_route, auth_route
from routes.admin import admin_route

from database.database import init_db, get_session
from fastapi.middleware.cors import CORSMiddleware
from services.logging.logging import get_logger
from services.service.mlmodelService import BaseMLModel
from services.service.UnitOfWork import UnitOfWork
from sqlmodel import Session

logging = get_logger(logger_name=__name__)


def create_app() -> FastAPI:
    # global _ml_model

    app = FastAPI()

    origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Healthcheck endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    # Передача зависимости
    app.include_router(home_route)
    app.include_router(auth_route)
    app.include_router(admin_route)

    return app


app = create_app()


@app.on_event("startup")
def on_startup():
    logging.info("Инициализация базы данных...")
    try:
        init_db()
        subprocess.run(["dvc", "pull"])
        logging.info("dvc pull")
        logging.info("Запуск приложения успешно завершен")
    except Exception as e:
        logging.error(f"Ошибка при запуске: {str(e)}")
        raise


if __name__ == "__main__":
    logging.info("api run")
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
