import flet as ft

from models.enums import TrustLevel
from theme import (
    COLOR_PRIMARY, COLOR_TEXT, COLOR_TEXT_MUTED,
    trust_badge, primary_button, secondary_button, page_view, icon_text,
)


def welcome_page(page: ft.Page, ds) -> ft.View:
    async def go_passport(e):
        await page.push_route("/passport")

    async def go_business(e):
        await page.push_route("/business")

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
            primary_button("I want to build my experience", go_passport, "SCHOOL"),
            secondary_button("I want to post a challenge", go_business, "BUSINESS_CENTER"),
        ],
        center=True,
    )