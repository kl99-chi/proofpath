import flet as ft

from models.challenge import MicroChallenge
from models.enums import ChallengeStatus
from theme import (
    COLOR_TEXT_MUTED, COLOR_ERROR,
    back_button, primary_button, page_view, app_bar,
)

# Hardcoded for the MVP.
CURRENT_BUSINESS_ID = "B001"

SKILL_OPTIONS = ["Excel", "Python", "SQL", "Design", "Networking"]

# What the business sees -> hours a youth has to submit after accepting.
TIME_LIMITS = {"24 hours": 24, "3 days": 72, "7 days": 168, "14 days": 336}


def post_challenge_page(page: ft.Page, ds) -> ft.View:
    async def go_business(e):
        await page.push_route("/business")

    title_field = ft.TextField(label="Title")
    skill_dropdown = ft.Dropdown(
        label="Skill needed",
        options=[ft.dropdown.Option(s) for s in SKILL_OPTIONS],
    )
    effort_field = ft.TextField(label="Estimated effort", hint_text="e.g. 1-2 hours")
    time_dropdown = ft.Dropdown(
        label="Time to submit after accepting",
        options=[ft.dropdown.Option(label) for label in TIME_LIMITS],
        value="24 hours",
    )
    deliverable_field = ft.TextField(label="Deliverable", hint_text="What should they submit?")
    outcome_field = ft.TextField(label="Learning outcome", hint_text="What will they practise or learn?")
    reward_field = ft.TextField(
        label="Reward (optional, disclosed upfront)",
        hint_text="e.g. R200 voucher or no reward",
    )

    error_text = ft.Text("", color=COLOR_ERROR)

    async def post(e):
        if not title_field.value or not skill_dropdown.value:
            error_text.value = "Title and skill are required."
            page.update()
            return

        new_id = f"CH{len(ds.challenges) + 1:03d}"
        challenge = MicroChallenge(
            id=new_id,
            business_id=CURRENT_BUSINESS_ID,
            title=title_field.value,
            skill_name=skill_dropdown.value,
            description=deliverable_field.value or "",
            estimated_effort=effort_field.value or "",
            deliverable=deliverable_field.value or "",
            learning_outcome=outcome_field.value or "",
            reward=reward_field.value or "No reward",
            status=ChallengeStatus.OPEN,
            time_limit_hours=TIME_LIMITS[time_dropdown.value or "24 hours"],
        )
        ds.challenges[challenge.id] = challenge
        ds.save()
        await page.push_route("/business")

    return page_view(
        "/post-challenge",
        [
            app_bar("Post a Challenge", "ROCKET_LAUNCH"),
            ft.Text(
                "Create a small, educational task with a clear outcome.",
                size=12,
                color=COLOR_TEXT_MUTED,
            ),
            title_field,
            skill_dropdown,
            effort_field,
            time_dropdown,
            ft.Text(
                "If a youth hasn't submitted anything by then, they're withdrawn "
                "automatically and the spot opens up for someone else.",
                size=12,
                color=COLOR_TEXT_MUTED,
            ),
            deliverable_field,
            outcome_field,
            reward_field,
            error_text,
            primary_button("Post learning challenge", post, "ROCKET_LAUNCH"),
            back_button(go_business),
        ],
    )