import uvicorn
import subprocess
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from routes.home import home_route, auth_route
from routes.admin import admin_route

from database.database import init_db, get_session
from fastapi.middleware.cors import CORSMiddleware
from services.logging.logging import get_logger
from services.service.mlmodelService import BaseMLModel
from services.service.UnitOfWork import UnitOfWork
from sqlmodel import Session
import os

logging = get_logger(logger_name=__name__)


def ensure_directories():
    """Создает необходимые директории если они не существуют"""
    directories = ["static", "static/images", "static/css", "static/js"]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory exists: {directory}")


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

    # static
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Передача зависимости
    app.include_router(home_route)
    app.include_router(auth_route)
    app.include_router(admin_route)

    # Добавим тестовый эндпоинт для проверки статических файлов
    @app.get("/test-static")
    async def test_static():
        import os

        static_exists = os.path.exists("static")
        images_exists = os.path.exists("static/images")

        files_in_static = []
        files_in_images = []

        if static_exists:
            files_in_static = os.listdir("static")

        if images_exists:
            files_in_images = os.listdir("static/images")

        return {
            "static_directory_exists": static_exists,
            "images_directory_exists": images_exists,
            "files_in_static": files_in_static,
            "files_in_images": files_in_images,
            "current_working_directory": os.getcwd(),
        }

    return app


app = create_app()


@app.on_event("startup")
def on_startup():
    logging.info("Инициализация базы данных...")
    try:
        init_db()
        subprocess.run(["dvc", "pull"])
        logging.info("dvc pull")
        ensure_directories()
        logging.info("Запуск приложения успешно завершен")

    except Exception as e:
        logging.error(f"Ошибка при запуске: {str(e)}")
        raise


if __name__ == "__main__":
    logging.info("api run")
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
