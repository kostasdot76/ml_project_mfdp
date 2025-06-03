import uvicorn
import subprocess
from fastapi import FastAPI, Depends
from routes.home import home_route, auth_route
from routes.admin import admin_route

from database.database import init_db, get_session
from fastapi.middleware.cors import CORSMiddleware
from services.logging.logging import get_logger

logging = get_logger(logger_name=__name__)

app = FastAPI()
app.include_router(home_route)
app.include_router(auth_route)
app.include_router(admin_route)
# app.include_router(user_route, prefix="/user")
# app.include_router(prediction_route, prefix="/prediction")

from auth.hash_password import HashPassword

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

hash_password = HashPassword()


@app.on_event("startup")
def on_startup():
    init_db()
    subprocess.run(["dvc", "pull"])
    logging.info("dvc pull")


if __name__ == "__main__":
    logging.info("api run")
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
