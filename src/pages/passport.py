import flet as ft

from models.enums import TrustLevel
from theme import (
    COLOR_PRIMARY, COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_SUCCESS, trust_badge, card,
    logout_button, primary_button, secondary_button, stat_strip, page_view,
    app_bar, icon, icon_text,
)


def passport_page(page: ft.Page, ds) -> ft.View:
    async def log_out(e):
        ds.logout()
        await page.push_route("/")

    async def go_challenges(e):
        await page.push_route("/challenges")

    async def go_add_skill(e):
        await page.push_route("/add-skill")

    youth = ds.youths[ds.current_profile_id]
    skills = [ds.skills[sid] for sid in youth.skill_ids]

    total_evidence = sum(len(s.evidence_ids) for s in skills)
    total_verified = sum(
        1 for s in skills if s.trust_level == TrustLevel.BUSINESS_VERIFIED
    )

    def proof_lines(skill):
        """The proof behind a skill: which business verified it for which
        task, and the person's own evidence entries."""
        lines = []
        for challenge_id in skill.verified_challenge_ids:
            ch = ds.challenges.get(challenge_id)
            if ch is None:
                continue
            business = ds.businesses.get(ch.business_id)
            who = business.name if business else "a business"
            lines.append(
                icon_text("VERIFIED", f"Verified by {who}: {ch.title}", size=12,
                          color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD)
            )
        for evidence_id in skill.evidence_ids:
            ev = ds.evidence.get(evidence_id)
            if ev is None:
                continue
            kind = ev.evidence_type.value.replace("_", " ").capitalize()
            lines.append(
                icon_text("ATTACH_FILE", f"{kind}: {ev.description}", size=12,
                          color=COLOR_TEXT_MUTED)
            )
        return lines

    skill_cards = []
    for skill in skills:
        if skill.trust_level == TrustLevel.BUSINESS_VERIFIED:
            count = len(skill.verified_challenge_ids)
            detail = f"{count} verified experience{'s' if count != 1 else ''}"
        elif skill.trust_level == TrustLevel.EVIDENCE_BACKED:
            count = len(skill.evidence_ids)
            detail = f"{count} project entr{'y' if count == 1 else 'ies'}"
        else:
            detail = "No evidence yet"

        card_controls = [
            ft.Row(
                controls=[
                    ft.Text(skill.name, weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT),
                    trust_badge(skill.trust_level),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Text(detail, size=12, color=COLOR_TEXT_MUTED),
        ] + proof_lines(skill)

        if skill.trust_level != TrustLevel.BUSINESS_VERIFIED:
            async def add_evidence_click(e, sid=skill.id):
                ds.selected_skill_id = sid
                await page.push_route("/add-evidence")

            card_controls.append(
                ft.TextButton(
                    "Add evidence",
                    on_click=add_evidence_click,
                    icon=icon("ADD_CIRCLE_OUTLINE"),
                    style=ft.ButtonStyle(color=COLOR_PRIMARY),
                )
            )

        skill_cards.append(card(ft.Column(controls=card_controls)))

    if not skill_cards:
        skill_cards.append(
            card(
                ft.Text(
                    "No skills yet. Add your first skill to start building proof.",
                    color=COLOR_TEXT_MUTED,
                )
            )
        )

    return page_view(
        "/passport",
        [
            app_bar("Experience Passport", "BADGE"),
            ft.Text(youth.name, size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            ft.Text(youth.headline, color=COLOR_TEXT, weight=ft.FontWeight.BOLD),
            stat_strip(
                [
                    (str(len(skills)), "Skills", "PSYCHOLOGY"),
                    (str(total_evidence), "Evidence", "ATTACH_FILE"),
                    (str(total_verified), "Verified", "VERIFIED"),
                ]
            ),
            ft.Text("My skills", weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            ft.Column(controls=skill_cards),
            primary_button("Browse Micro-Challenges", go_challenges, "SEARCH"),
            secondary_button("Add a skill", go_add_skill, "ADD"),
            logout_button(log_out),
        ],
    )