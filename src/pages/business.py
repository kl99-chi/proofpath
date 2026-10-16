import flet as ft

from models.enums import SubmissionStatus
from theme import (
    COLOR_TEXT, COLOR_TEXT_MUTED, challenge_badge, accepted_counter, card,
    back_button, primary_button, secondary_button, stat_strip, page_view,
    app_bar, icon_text,
)

# Hardcoded for the MVP: always viewing Lerato's Kitchen.
CURRENT_BUSINESS_ID = "B001"


def business_page(page: ft.Page, ds) -> ft.View:
    async def go_home(e):
        await page.push_route("/")

    async def go_post_challenge(e):
        await page.push_route("/post-challenge")

    async def go_review(e):
        await page.push_route("/review")

    business = ds.businesses[CURRENT_BUSINESS_ID]
    challenges = [
        c for c in ds.challenges.values() if c.business_id == CURRENT_BUSINESS_ID
    ]
    my_ids = {c.id for c in challenges}

    waiting = sum(
        1
        for s in ds.submissions.values()
        if s.status == SubmissionStatus.SUBMITTED
        and s.challenge_id in my_ids
        and not ds.challenges[s.challenge_id].is_solved
    )
    solved = sum(1 for c in challenges if c.is_solved)

    challenge_cards = []
    for ch in challenges:
        challenge_cards.append(
            card(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(ch.title, weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT),
                                challenge_badge(ch.is_solved),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text(
                            f"Skill: {ch.skill_name} · Est. {ch.estimated_effort}",
                            size=12,
                            color=COLOR_TEXT_MUTED,
                        ),
                        accepted_counter(ch),
                    ]
                )
            )
        )
    if not challenge_cards:
        challenge_cards.append(ft.Text("No challenges posted yet.", color=COLOR_TEXT_MUTED))

    return page_view(
        "/business",
        [
            app_bar("Business Workspace", "BUSINESS_CENTER"),
            ft.Text(business.name, size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            icon_text("LOCATION_ON", business.location, color=COLOR_TEXT_MUTED),
            ft.Container(height=8),
            stat_strip(
                [
                    (str(len(challenges)), "Posted", "LIST_ALT"),
                    (str(waiting), "Waiting", "HOURGLASS_EMPTY"),
                    (str(solved), "Solved", "CHECK_CIRCLE"),
                ]
            ),
            ft.Text("My posted challenges", weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            ft.Column(controls=challenge_cards),
            primary_button("Post a Challenge", go_post_challenge, "ADD"),
            secondary_button("Review & Verify", go_review, "RATE_REVIEW"),
            back_button(go_home),
        ],
    )