import flet as ft

from models.enums import TrustLevel
from pages.auth import home_route
from theme import (
    COLOR_PRIMARY, COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ERROR,
    trust_badge, primary_button, secondary_button, page_view, icon_text,
)


def welcome_page(page: ft.Page, ds) -> ft.View:
    error_text = ft.Text("", color=COLOR_ERROR, size=12, text_align=ft.TextAlign.CENTER)

    async def go_signup_youth(e):
        await page.push_route("/signup-youth")

    async def go_signup_business(e):
        await page.push_route("/signup-business")

    async def go_login(e):
        await page.push_route("/login")

    async def go_my_home(e):
        await page.push_route(home_route(ds.current_account))

    async def log_out(e):
        ds.logout()
        # Already on "/", so rebuild this page instead of navigating.
        page.views[-1] = welcome_page(page, ds)
        page.update()

    async def sign_in_demo(profile_id: str):
        try:
            account = ds.sign_in_as(profile_id)
        except ValueError as ex:
            error_text.value = str(ex)
            page.update()
            return
        await page.push_route(home_route(account))

    async def demo_youth(e):
        await sign_in_demo("Y001")

    async def demo_business(e):
        await sign_in_demo("B001")

    if ds.current_account:
        actions = [
            ft.Text(f"Signed in as {ds.current_name}", color=COLOR_TEXT,
                    weight=ft.FontWeight.BOLD),
            primary_button("Continue", go_my_home, "ARROW_FORWARD"),
            secondary_button("Log out", log_out, "LOGOUT"),
        ]
    else:
        actions = [
            primary_button("I want to build my experience", go_signup_youth, "SCHOOL"),
            secondary_button("I want to post a challenge", go_signup_business, "BUSINESS_CENTER"),
            ft.TextButton(
                "I already have an account. Log in",
                on_click=go_login,
                style=ft.ButtonStyle(color=COLOR_PRIMARY),
            ),
            ft.Container(height=8),
            ft.Text("TRY THE DEMO", size=11, color=COLOR_TEXT_MUTED,
                    weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    secondary_button("Thabo (youth)", demo_youth, "PERSON"),
                    secondary_button("Lerato's Kitchen (business)", demo_business, "STOREFRONT"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True,
            ),
            error_text,
        ]

    return page_view(
        "/",
        [
            ft.Container(height=24),
            icon_text("TRENDING_UP", "ProofPath", size=22, color=COLOR_PRIMARY,
                      weight=ft.FontWeight.BOLD, center=True),
            ft.Text("YOUR EXPERIENCE COUNTS", size=11, weight=ft.FontWeight.BOLD,
                    color=COLOR_PRIMARY, text_align=ft.TextAlign.CENTER),
            ft.Text(
                "Turn what you've done into proof of what you can do.",
                size=32,
                weight=ft.FontWeight.BOLD,
                color=COLOR_TEXT,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Every skill moves up a ladder as your evidence gets stronger:",
                color=COLOR_TEXT_MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Row(
                controls=[
                    trust_badge(TrustLevel.SELF_DECLARED),
                    trust_badge(TrustLevel.EVIDENCE_BACKED),
                    trust_badge(TrustLevel.BUSINESS_VERIFIED),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True,
            ),
            ft.Container(height=24),
            *actions,
        ],
        center=True,
    )