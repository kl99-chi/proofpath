import flet as ft

from models.enums import Role
from services.auth import MIN_PASSWORD_LENGTH
from services.data_service import DEMO_PASSWORD
from theme import (
    COLOR_PRIMARY, COLOR_TEXT_MUTED, COLOR_ERROR,
    page_view, app_bar, primary_button, back_button,
)


def home_route(account) -> str:
    """Where a signed-in person lands."""
    return "/passport" if account.role == Role.YOUTH else "/business"


def login_page(page: ft.Page, ds) -> ft.View:
    async def go_welcome(e):
        await page.push_route("/")

    email_field = ft.TextField(label="Email", autofocus=True)
    password_field = ft.TextField(label="Password", password=True, can_reveal_password=True)
    error_text = ft.Text("", color=COLOR_ERROR, size=12)

    async def log_in(e):
        try:
            account = ds.login(email_field.value, password_field.value)
        except ValueError as ex:
            error_text.value = str(ex)
            page.update()
            return
        await page.push_route(home_route(account))

    password_field.on_submit = log_in  # Enter key submits

    return page_view(
        "/login",
        [
            app_bar("Log in", "LOGIN"),
            ft.Container(height=8),
            email_field,
            password_field,
            error_text,
            primary_button("Log in", log_in, "LOGIN"),
            ft.TextButton(
                "New here? Create an account",
                on_click=go_welcome,
                style=ft.ButtonStyle(color=COLOR_PRIMARY),
            ),
            ft.Text(
                f"Prototype demo accounts (password {DEMO_PASSWORD}): "
                f"thabo@proofpath.demo (youth), lerato@proofpath.demo (business)",
                size=12,
                color=COLOR_TEXT_MUTED,
            ),
            back_button(go_welcome),
        ],
    )


def signup_page(page: ft.Page, ds, role: Role) -> ft.View:
    is_youth = role == Role.YOUTH
    route = "/signup-youth" if is_youth else "/signup-business"

    async def go_welcome(e):
        await page.push_route("/")

    async def go_login(e):
        await page.push_route("/login")

    name_field = ft.TextField(
        label="Full name" if is_youth else "Business name", autofocus=True
    )
    extra_field = ft.TextField(
        label="Headline (e.g. IT Graduate)" if is_youth
        else "Location (e.g. Soweto, Johannesburg)"
    )
    email_field = ft.TextField(label="Email")
    password_field = ft.TextField(label="Password", password=True, can_reveal_password=True)
    confirm_field = ft.TextField(label="Confirm password", password=True, can_reveal_password=True)
    error_text = ft.Text("", color=COLOR_ERROR, size=12)

    async def create_account(e):
        if password_field.value != confirm_field.value:
            error_text.value = "The two passwords don't match."
            page.update()
            return
        try:
            account = ds.register(
                role, name_field.value, email_field.value,
                password_field.value, extra_field.value or "",
            )
        except ValueError as ex:
            error_text.value = str(ex)
            page.update()
            return
        await page.push_route(home_route(account))

    confirm_field.on_submit = create_account

    notice = []
    if not is_youth:
        notice = [
            ft.Text(
                "By posting on ProofPath you agree that challenges are small, "
                "clearly scoped learning tasks, not a way to get unpaid work "
                "done for a normal job.",
                size=12,
                color=COLOR_TEXT_MUTED,
            )
        ]

    return page_view(
        route,
        [
            app_bar("Create youth account" if is_youth else "Create business account",
                    "PERSON_ADD"),
            ft.Container(height=8),
            name_field,
            extra_field,
            email_field,
            password_field,
            ft.Text(f"At least {MIN_PASSWORD_LENGTH} characters.", size=12, color=COLOR_TEXT_MUTED),
            confirm_field,
            *notice,
            error_text,
            primary_button("Create account", create_account, "PERSON_ADD"),
            ft.TextButton(
                "Already have an account? Log in",
                on_click=go_login,
                style=ft.ButtonStyle(color=COLOR_PRIMARY),
            ),
            back_button(go_welcome),
        ],
    )


def access_denied_page(page: ft.Page, ds) -> ft.View:
    async def go_login(e):
        await page.push_route("/login")

    async def go_welcome(e):
        await page.push_route("/")

    async def go_my_home(e):
        await page.push_route(home_route(ds.current_account))

    account = ds.current_account
    if account is None:
        message = "Please log in to see this page."
        actions = [primary_button("Log in", go_login, "LOGIN"), back_button(go_welcome)]
    else:
        message = "This page is for a different type of account."
        actions = [primary_button("Go to my home", go_my_home, "HOME")]

    return page_view(
        page.route,
        [app_bar("Access restricted", "LOCK"), ft.Container(height=8),
         ft.Text(message, color=COLOR_TEXT_MUTED), *actions],
    )