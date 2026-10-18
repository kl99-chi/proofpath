import flet as ft

from models.skill import SKILL_CATALOG
from theme import (
    COLOR_TEXT_MUTED, COLOR_ERROR,
    back_button, primary_button, page_view, app_bar,
)


def add_skill_page(page: ft.Page, ds) -> ft.View:
    async def go_passport(e):
        await page.push_route("/passport")

    youth = ds.youths[ds.current_profile_id]
    have = {ds.skills[sid].name for sid in youth.skill_ids}
    available = [s for s in SKILL_CATALOG if s not in have]

    if not available:
        return page_view(
            "/add-skill",
            [
                app_bar("Add a skill", "ADD_CIRCLE_OUTLINE"),
                ft.Text("You've already added every skill ProofPath currently offers.",
                        color=COLOR_TEXT_MUTED),
                back_button(go_passport),
            ],
        )

    dropdown = ft.Dropdown(
        label="Skill",
        options=[ft.dropdown.Option(s) for s in available],
    )
    error_text = ft.Text("", color=COLOR_ERROR, size=12)

    async def add(e):
        if not dropdown.value:
            error_text.value = "Pick a skill first."
            page.update()
            return
        ds.add_skill(youth.id, dropdown.value)
        await page.push_route("/passport")

    return page_view(
        "/add-skill",
        [
            app_bar("Add a skill", "ADD_CIRCLE_OUTLINE"),
            ft.Text(
                "New skills start as Self-declared (○). Add evidence or complete "
                "a business challenge to move them up.",
                size=12,
                color=COLOR_TEXT_MUTED,
            ),
            dropdown,
            error_text,
            primary_button("Add skill", add, "ADD"),
            back_button(go_passport),
        ],
    )