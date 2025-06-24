import time
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from auth.authenticate import authenticate_cookie, authenticate_cookie_admin
from auth.hash_password import HashPassword
from auth.jwt_handler import create_access_token
from database.database import get_session
from services.auth.loginform import LoginForm
from services.crud import UserRepository
from services.service import (
    UnitOfWork,
    DepositTransactionService,
    CreatePredictionTask,
    get_uow,
)
from models.schemas import PredictionRequest
from schemas.promptSchemas import PromptEnhancerInput
from models.enums import UserRole
from database.config import get_settings
from services.auth.depositform import DepositForm
from services.auth.predictionform import PredictionForm
from services.service.mlmodelService import BaseMLModel
from fastapi import Form
from services.logging.logging import get_logger
from markdown import markdown

logging = get_logger(logger_name=__name__)

settings = get_settings()
home_route = APIRouter()
home_route.mount("/static", StaticFiles(directory="static"), name="static")
auth_route = APIRouter(prefix="/auth", tags=["Auth"])
auth_route.mount("/static", StaticFiles(directory="static"), name="static")

hash_password = HashPassword()
templates = Jinja2Templates(directory="view")

templates.env.filters["markdown"] = lambda text: markdown(text)

"""
# Для генерации изображений
result = {"image": "images/generated_123.png"}

# Для улучшения промптов
result = {"prompt": "### Улучшенный промпт\n\nОписание изображения..."}
"""


@home_route.get("/", response_class=HTMLResponse)
async def index(request: Request, session=Depends(get_session)):
    token = request.cookies.get(settings.COOKIE_NAME)
    if token:
        email = await authenticate_cookie(token)
    else:
        email = None

    context = {"user": email, "request": request}

    user = UserRepository(session).get_user_by_email(email)

    if user and user.role == UserRole.ADMIN:
        return templates.TemplateResponse("admin.html", context)

    return templates.TemplateResponse("index.html", context)


@home_route.post("/token")
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session=Depends(get_session),
) -> dict[str, str]:
    if not form_data.username.__contains__("@"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Email required"
        )
    user_exist = UserRepository(session).get_user_by_email(form_data.username)
    if user_exist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )

    if hash_password.verify_hash(form_data.password, user_exist.password):
        access_token = create_access_token(user_exist.email)
        response.set_cookie(
            key=settings.COOKIE_NAME, value=f"Bearer {access_token}", httponly=True
        )

        return {settings.COOKIE_NAME: access_token, "token_type": "bearer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid details passed."
    )


@auth_route.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    context = {
        "request": request,
    }
    return templates.TemplateResponse("login.html", context)


@auth_route.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, session=Depends(get_session)):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            response = RedirectResponse("/", status.HTTP_302_FOUND)
            await login_for_access_token(
                response=response, form_data=form, session=session
            )
            form.__dict__.update(msg="Login Successful!")
            logging.info("[green]Login successful!!!!")
            return response
        except HTTPException:
            form.__dict__.update(msg="")
            form.__dict__.get("errors").append("Incorrect Email or Password")
            return templates.TemplateResponse(
                "login.html", form.__dict__, status_code=status.HTTP_401_UNAUTHORIZED
            )

    return templates.TemplateResponse("login.html", form.__dict__)


@auth_route.get("/logout", response_class=HTMLResponse)
async def login_get():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(settings.COOKIE_NAME)
    return response


@auth_route.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@auth_route.post("/signup", response_class=HTMLResponse)
async def signup_post(request: Request, session=Depends(get_session)):
    form = await request.form()
    user_data = {"email": form.get("email"), "password": form.get("password")}
    logging.info(f"signup, get user data {user_data}")
    try:
        UserRepository(session).register_user(user_data["email"], user_data["password"])
        session.commit()
        logging.info(f"signup, user created")
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        return templates.TemplateResponse(
            "signup.html", {"request": request, "errors": [str(e)]}
        )


@home_route.post("/balance/deposit")
async def deposit_balance(
    request: Request,
    email: str = Depends(authenticate_cookie),
    session=Depends(get_session),
):
    user = UserRepository(session).get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )

    form = DepositForm(request)
    await form.load_data()

    if not await form.is_valid():
        return templates.TemplateResponse(
            "balance.html",
            {"request": request, "errors": form.errors, "balance": user.balance},
        )

    try:
        with UnitOfWork(session) as uow:
            deposit_service = DepositTransactionService(
                user=user, uow=uow, amount=form.amount
            )

            if deposit_service.process():
                return RedirectResponse(
                    url="/balance", status_code=status.HTTP_302_FOUND
                )
            raise HTTPException(status_code=400, detail="Deposit failed")
    except Exception as e:
        return templates.TemplateResponse(
            "balance.html", {"request": request, "error": str(e)}
        )


@home_route.get("/balance", response_class=HTMLResponse)
async def balance_page(
    request: Request,
    email: str = Depends(authenticate_cookie),
    session=Depends(get_session),
):
    user = UserRepository(session).get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )

    return templates.TemplateResponse(
        "balance.html", {"request": request, "balance": user.balance, "user": email}
    )


@home_route.get("/predict", response_class=HTMLResponse)
async def predict_page(request: Request, user: str = Depends(authenticate_cookie)):
    return templates.TemplateResponse(
        "predict.html", {"request": request, "user": user}
    )


@home_route.post("/predict", response_class=HTMLResponse)
async def create_prediction_front(
    request: Request,
    model_type: str = Form(...),
    prompt: str = Form(...),
    include_color_instruction: bool = Form(False),
    replace_colors_with_hex: bool = Form(True),
    # negative_prompt: str = "text, watermark, signature, blur",
    email: str = Depends(authenticate_cookie),
    # uow: UnitOfWork = Depends(get_uow),
    session=Depends(get_session),
):
    try:
        logging.info(
            f"Данные формы {prompt} {include_color_instruction}  {replace_colors_with_hex}"
        )

        # input_data = json.loads(data)

        # prediction_request = PromptEnhancerInput(
        #     prompt_ru=prompt_ru,
        #     include_color_instruction=include_color_instruction,
        #     replace_colors_with_hex=replace_colors_with_hex,
        # )
        # input_data = json.dumps(prediction_request)
        if model_type == "prompt_enhancer":
            input_data = json.dumps(
                {
                    "prompt_ru": prompt,
                    "include_color_instruction": include_color_instruction,
                    "replace_colors_with_hex": replace_colors_with_hex,
                }
            )
        else:
            input_data = json.dumps(
                {
                    "prompt": prompt,
                    "order_id": 0,
                    "negative_prompt": "text, watermark, signature, blur",
                }
            )
        logging.info(f"Данные для формы predict приняты {input_data}")
        with UnitOfWork(session) as uow:
            user = uow.users.get_user_by_email(email)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
                )

            # Создаём задачу
            logging.info(f" Создаём задачу task = CreatePredictionTask(: {user}")
            task = CreatePredictionTask(
                user=user,
                uow=uow,
                data=PredictionRequest(input_data=input_data, model_type=model_type),
            )

            # Инициализация init_rabbitmq
            logging.info(f"Инициализация init_rabbitmq")
            task.init_rabbitmq()
            # Отправляем заказ в очередь
            logging.info(f"Отправляем заказ в очередь")
            if task.process():
                logging.info(f"Заказ успешно отправлен в очередь")
                return RedirectResponse(
                    url=f"/predict/status/{task.prediction.id}",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

    except json.JSONDecodeError:
        return templates.TemplateResponse(
            "predict.html", {"request": request, "errors": ["Invalid data format"]}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "predict.html", {"request": request, "error": str(e)}
        )
    # finally:
    #     task.close()


@home_route.get("/predict/status/{task_id}", response_class=HTMLResponse)
async def get_prediction_status_front(
    task_id: int,
    request: Request,
    email: str = Depends(authenticate_cookie),
    session=Depends(get_session),
):
    try:
        with UnitOfWork(session) as uow:
            prediction = uow.predictions.get_by_id(task_id)
            user = uow.users.get_user_by_email(email)

            if not prediction or prediction.user_id != user.id:
                raise HTTPException(status_code=404, detail="Task not found")

            logging.info(f"prediction.result Is {prediction.result}")
            # выделеим результат
            result_obj = None
            if prediction.result:
                try:
                    result_obj = json.loads(prediction.result)
                except json.JSONDecodeError:
                    result_obj = {"error": "Invalid result format"}
            logging.info(f" result_obj {result_obj}")
            return templates.TemplateResponse(
                "status.html",
                {
                    "request": request,
                    "prediction": prediction,
                    "result_obj": result_obj,
                },
            )
    except Exception as e:
        logging.error(f"Error in prediction status endpoint: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e), "task_id": task_id}
        )


@home_route.get("/predict/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    email: str = Depends(authenticate_cookie),
    session=Depends(get_session),
):
    try:
        with UnitOfWork(session) as uow:
            user = uow.users.get_user_by_email(email)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
                )
            logging.info(f"_______user {user}")
            predictions = uow.predictions.get_user_entities(user.id)

            logging.info(f"______predictions {predictions}")
            return templates.TemplateResponse(
                "history.html",
                {"request": request, "predictions": predictions, "user": email},
            )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )
