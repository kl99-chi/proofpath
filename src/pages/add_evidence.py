import flet as ft

from models.evidence import Evidence, EvidenceType
from theme import (
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ERROR,
    trust_badge, card, back_button, primary_button, page_view, app_bar,
)


def add_evidence_page(page: ft.Page, ds) -> ft.View:
    async def go_passport(e):
        await page.push_route("/passport")

    skill_id = ds.selected_skill_id
    if skill_id is None or skill_id not in ds.skills:
        return page_view(
            "/add-evidence",
            [
                app_bar("Add Evidence", "ADD_CIRCLE_OUTLINE"),
                ft.Text("No skill selected.", color=COLOR_TEXT_MUTED),
                back_button(go_passport),
            ],
        )

    skill = ds.skills[skill_id]

    experience_type = ft.RadioGroup(
        content=ft.Column(
            controls=[
                ft.Radio(value=EvidenceType.ACADEMIC_PROJECT.value, label="Academic project"),
                ft.Radio(value=EvidenceType.PERSONAL_PROJECT.value, label="Personal project"),
                ft.Radio(value=EvidenceType.INFORMAL_EXPERIENCE.value, label="Informal experience"),
            ]
        ),
        value=EvidenceType.ACADEMIC_PROJECT.value,
    )

    description_field = ft.TextField(label="What did you do?", multiline=True)
    error_text = ft.Text("", color=COLOR_ERROR, size=12)

    async def save(e):
        description = (description_field.value or "").strip()
        if not description:
            error_text.value = "Describe what you did. Evidence needs some detail."
            page.update()
            return

        new_id = f"EV{len(ds.evidence) + 1:03d}"
        evidence = Evidence(
            id=new_id,
            owner_id=skill.owner_id,
            skill_id=skill.id,
            evidence_type=EvidenceType(experience_type.value),
            description=description,
        )
        ds.evidence[evidence.id] = evidence
        skill.add_evidence(evidence.id)
        ds.save()
        ds.selected_skill_id = None
        await page.push_route("/passport")

    return page_view(
        "/add-evidence",
        [
            app_bar(f"Add Evidence: {skill.name}", "ADD_CIRCLE_OUTLINE"),
            card(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(skill.name, weight=ft.FontWeight.BOLD, size=18, color=COLOR_TEXT),
                                trust_badge(skill.trust_level),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text("Add proof to move this skill up.", size=12, color=COLOR_TEXT_MUTED),
                    ]
                )
            ),
            ft.Text("What kind of experience was it?", weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            experience_type,
            description_field,
            error_text,
            primary_button("Save evidence", save, "SAVE"),
            back_button(go_passport),
        ],
    )