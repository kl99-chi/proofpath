import re

import flet as ft

from models.skill import SKILL_CATALOG
from theme import (
    COLOR_TEXT_MUTED, COLOR_ERROR,
    back_button, primary_button, page_view, app_bar,
)

OTHER = "Other (type your own)"
MAX_CUSTOM_LENGTH = 40
_ALLOWED = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 +#./&'-]*$")

# Rule-based suggestions: words in a youth's headline (their qualification)
# mapped to the skills most likely to fit. A learned model can replace this
# later; the page only needs suggest_skills() to keep its signature.
SUGGESTION_RULES = [
    ({"it", "ict", "software", "developer", "programming", "computer",
      "computing", "engineering"},
     ["Python", "SQL", "Web Development", "Networking", "Excel"]),
    ({"business", "commerce", "accounting", "finance", "bookkeeping"},
     ["Excel", "Bookkeeping", "Data Entry", "Social Media"]),
    ({"design", "designer", "art", "creative", "media", "marketing"},
     ["Design", "Social Media", "Writing"]),
    ({"admin", "administration", "office", "clerk", "secretary"},
     ["Data Entry", "Excel", "Writing"]),
]


def suggest_skills(headline: str, available: list[str]) -> list[str]:
    """Skills from `available` that fit the headline, best matches first."""
    words = set(re.findall(r"[a-z]+", (headline or "").lower()))
    suggested: list[str] = []
    for keywords, skills in SUGGESTION_RULES:
        if words & keywords:
            for skill in skills:
                if skill in available and skill not in suggested:
                    suggested.append(skill)
    return suggested


def clean_custom_skill(raw: str, have: set[str], catalog: list[str]):
    """Validate a typed-in skill. Returns (skill_name, None) or (None, error)."""
    name = " ".join((raw or "").split())  # trim and collapse spaces
    if len(name) < 2:
        return None, "Type your skill (at least 2 characters)."
    if len(name) > MAX_CUSTOM_LENGTH:
        return None, f"Keep it under {MAX_CUSTOM_LENGTH} characters."
    if not _ALLOWED.match(name):
        return None, "Use letters, numbers and spaces only (plus + # . / & ' -)."
    # If it matches a catalog skill, use the catalog spelling so business
    # challenges (matched by name) still find it.
    for known in catalog:
        if known.lower() == name.lower():
            name = known
            break
    if name.lower() in {h.lower() for h in have}:
        return None, f"{name} is already on your passport."
    return name, None


def add_skill_page(page: ft.Page, ds) -> ft.View:
    async def go_passport(e):
        await page.push_route("/passport")

    youth = ds.youths[ds.current_profile_id]
    have = {ds.skills[sid].name for sid in youth.skill_ids}
    available = [s for s in SKILL_CATALOG if s not in have]

    suggested = suggest_skills(youth.headline, available)
    ordered = suggested + [s for s in available if s not in suggested]

    dropdown = ft.Dropdown(
        label="Skill",
        options=[ft.dropdown.Option(s) for s in ordered] + [ft.dropdown.Option(OTHER)],
    )
    custom_field = ft.TextField(
        label="Your skill",
        hint_text="e.g. Photography",
        max_length=MAX_CUSTOM_LENGTH,
        visible=False,
    )
    error_text = ft.Text("", color=COLOR_ERROR, size=12)

    def on_skill_selected(e):
        custom_field.visible = dropdown.value == OTHER
        error_text.value = ""
        page.update()

    dropdown.on_select = on_skill_selected

    async def add(e):
        error_text.value = ""
        if not dropdown.value:
            error_text.value = "Pick a skill first."
            page.update()
            return
        if dropdown.value == OTHER:
            skill, problem = clean_custom_skill(custom_field.value, have, SKILL_CATALOG)
            if problem:
                error_text.value = problem
                page.update()
                return
        else:
            skill = dropdown.value
        ds.add_skill(youth.id, skill)
        await page.push_route("/passport")

    controls = [
        app_bar("Add a skill", "ADD_CIRCLE_OUTLINE"),
        ft.Text(
            "New skills start as Self-declared. Add evidence or complete "
            "a business challenge to move them up.",
            size=12,
            color=COLOR_TEXT_MUTED,
        ),
    ]
    if suggested:
        controls.append(
            ft.Text(
                f"Suggested for {youth.headline}: {', '.join(suggested)}",
                size=12,
                color=COLOR_TEXT_MUTED,
            )
        )
    controls += [
        dropdown,
        custom_field,
        error_text,
        primary_button("Add skill", add, "ADD"),
        back_button(go_passport),
    ]
    return page_view("/add-skill", controls)