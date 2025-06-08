from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database.database import get_session
from services.service import UnitOfWork, AdminService
from decimal import Decimal
from auth.authenticate import authenticate_cookie_admin

templates = Jinja2Templates(directory="view")

admin_route = APIRouter(prefix="/admin", tags=["Admin"])


@admin_route.get("/", response_class=HTMLResponse)
async def balance_page(
    request: Request, email: str = Depends(authenticate_cookie_admin)
):
    return templates.TemplateResponse("admin.html", {"request": request})


@admin_route.get("/users")
async def get_all_users(
    admin: str = Depends(authenticate_cookie_admin), session=Depends(get_session)
):
    return UnitOfWork(session).users.get_all_users()


@admin_route.get("/balance", response_class=HTMLResponse)
async def balance_page(
    request: Request,
    success: Optional[str] = None,
    email: str = Depends(authenticate_cookie_admin),
    session=Depends(get_session),
):

    return templates.TemplateResponse(
        "admin_balance.html", {"request": request, "success": success}
    )


@admin_route.post("/balance", response_class=HTMLResponse)
async def update_user_balance(
    request: Request,
    admin: str = Depends(authenticate_cookie_admin),
    session=Depends(get_session),
):
    form = await request.form()
    email = form.get("email")
    amount = Decimal(form.get("amount"))

    if amount <= 0:
        return templates.TemplateResponse(
            "admin_balance.html",
            {"request": request, "error": "Сумма должна быть больше нуля"},
        )

    with UnitOfWork(session) as uow:
        user = uow.users.get_user_by_email(email)
        if not user:
            return templates.TemplateResponse(
                "admin_balance.html",
                {"request": request, "error": "Пользователь не найден"},
            )

        # Обновление баланса
        admin_user = uow.users.get_user_by_email(admin)
        admin_service = AdminService(admin_user, uow)
        if admin_service.deposit_to_user(user.id, amount):
            return RedirectResponse(
                url="/admin/balance?success=Баланс+успешно+пополнен", status_code=303
            )
        else:
            return templates.TemplateResponse(
                "admin_balance.html",
                {"request": request, "error": "операция отклонена"},
            )


@admin_route.get("/transactions")
async def get_all_transactions(
    admin: str = Depends(authenticate_cookie_admin), session=Depends(get_session)
):
    return UnitOfWork(session).transactions.get_all_transactions()
