import os
import subprocess
import sys

import flet as ft

from models.enums import SubmissionStatus
from theme import (
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_SUCCESS, COLOR_PRIMARY, COLOR_ERROR,
    trust_tracker, card, back_button, pill, info_section, avatar, divider,
    secondary_button, page_view, app_bar, icon, accepted_counter,
)

CURRENT_BUSINESS_ID = "B001"


def open_file(path) -> None:
    """Open a file with the computer's default app."""
    if hasattr(os, "startfile"):  # Windows
        os.startfile(path)
    elif sys.platform == "darwin":  # macOS
        subprocess.run(["open", str(path)], check=False)
    else:  # Linux
        subprocess.run(["xdg-open", str(path)], check=False)


def review_verify_page(page: ft.Page, ds) -> ft.View:
    async def go_business(e):
        await page.push_route("/business")

    def refresh():
        page.views[-1] = review_verify_page(page, ds)
        page.update()

    def challenge_of(sub):
        return ds.challenges[sub.challenge_id]

    def has_matching_skill(sub):
        wanted = challenge_of(sub).skill_name
        return any(
            s.owner_id == sub.youth_id and s.name == wanted
            for s in ds.skills.values()
        )

    # Submissions waiting on this business, on challenges not yet solved.
    waiting = [
        sub
        for sub in ds.submissions.values()
        if sub.status == SubmissionStatus.SUBMITTED
        and challenge_of(sub).business_id == CURRENT_BUSINESS_ID
        and not challenge_of(sub).is_solved
    ]
    ready = [s for s in waiting if has_matching_skill(s)]
    blocked = [s for s in waiting if not has_matching_skill(s)]

    if not ready:
        message = "Nothing waiting for review right now."
        if blocked:
            message += (
                f" ({len(blocked)} submission(s) can't be reviewed yet: the "
                f"youth hasn't added the matching skill to their profile.)"
            )
        return page_view(
            "/review",
            [
                app_bar("Review & Verify", "RATE_REVIEW"),
                ft.Text(message, color=COLOR_TEXT_MUTED),
                back_button(go_business),
            ],
        )

    submission = ready[0]  # oldest first
    ch = challenge_of(submission)
    youth = ds.youths[submission.youth_id]
    skill = next(
        s for s in ds.skills.values()
        if s.owner_id == youth.id and s.name == ch.skill_name
    )
    trust_before = skill.trust_level

    # This youth's earlier attempts on this challenge, oldest first.
    past_attempts = [
        s for s in ds.submissions_for(ch.id, youth.id)
        if s.attempt_number < submission.attempt_number
    ]

    attempt_label = (
        f" · Attempt {submission.attempt_number}"
        if submission.attempt_number > 1
        else ""
    )

    # ---------- reusable pieces ----------
    def build_attachment(sub):
        """Filename plus an Open button for one submission's file."""
        file_path = ds.attachment_path(sub)
        if not file_path.exists():
            return ft.Text(
                f"{sub.attachment_name} (file not found in data/uploads)",
                color=COLOR_ERROR,
            )

        error = ft.Text("", color=COLOR_ERROR, size=12)

        async def open_it(e, p=file_path, err=error):
            try:
                open_file(p)
            except OSError as ex:
                err.value = f"Couldn't open the file: {ex}"
                page.update()

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(sub.attachment_name, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                        secondary_button("Open file", open_it, "FOLDER_OPEN"),
                    ],
                    wrap=True,
                ),
                error,
            ]
        )

    def build_past_attempt(sub):
        """One earlier attempt: its note, its file, and the change requested."""
        parts = [
            ft.Text(f"ATTEMPT {sub.attempt_number}", size=12,
                    weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            info_section(
                "SUBMITTED NOTE",
                ft.Text(sub.note or "No note added.", color=COLOR_TEXT),
                icon_name="NOTES",
            ),
        ]
        if sub.has_attachment:
            parts.append(info_section("ATTACHMENT", build_attachment(sub), icon_name="ATTACH_FILE"))
        if sub.feedback:
            parts.append(
                info_section(
                    "REQUESTED CHANGE",
                    ft.Text(sub.feedback, color=COLOR_TEXT),
                    tint="#FFF4E0",
                    icon_name="CHAT_BUBBLE_OUTLINE",
                )
            )
        return ft.Container(
            content=ft.Column(controls=parts, spacing=8),
            bgcolor="#F5F0E8",
            padding=12,
            border_radius=10,
        )

    # ---------- the top card, built section by section ----------
    sections = [
        info_section(
            "TASK",
            ft.Column(
                controls=[
                    ft.Text(ch.title, size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                    ft.Row(controls=[pill(ch.skill_name, COLOR_PRIMARY)]),
                    accepted_counter(ch),
                ],
                spacing=6,
            ),
            icon_name="TASK_ALT",
        ),
        divider(),
        info_section(
            "SUBMITTED BY",
            ft.Row(
                controls=[
                    avatar(youth.name),
                    ft.Column(
                        controls=[
                            ft.Text(youth.name, weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT),
                            ft.Text(f"Submitted for review{attempt_label}", size=12, color=COLOR_TEXT_MUTED),
                        ],
                        spacing=2,
                    ),
                ],
            ),
            icon_name="PERSON",
        ),
        divider(),
    ]

    if past_attempts:
        sections += [
            info_section(
                f"PREVIOUS ATTEMPTS ({len(past_attempts)})",
                ft.Column(
                    controls=[build_past_attempt(sub) for sub in past_attempts],
                    spacing=8,
                ),
                icon_name="HISTORY",
            ),
            ft.Container(height=12),
        ]

    current_label = (
        "SUBMITTED NOTE"
        if submission.attempt_number == 1
        else f"SUBMITTED NOTE (ATTEMPT {submission.attempt_number})"
    )
    current_parts = [ft.Text(submission.note or "No note added.", color=COLOR_TEXT)]
    if submission.has_attachment:
        current_parts.append(build_attachment(submission))
    sections.append(
        info_section(
            current_label,
            ft.Column(controls=current_parts, spacing=6),
            tint="#E8F4EE",
            icon_name="NOTES",
        )
    )

    # ---------- actions ----------
    others = ch.accepted_count - 1  # other youths who accepted this challenge

    async def verify(e):
        submission.verify()
        ch.mark_verified()
        skill.verify_via_challenge(ch.id)
        ds.save()
        # Show a brief success state instead of instantly rebuilding,
        # so the moment actually registers.
        success_lines = [
            ft.Icon(icon("CHECK_CIRCLE"), size=64, color=COLOR_SUCCESS),
            ft.Text(
                f"{ch.skill_name} is now Business-verified",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=COLOR_TEXT,
            ),
            ft.Text(
                f"{youth.name} demonstrated this skill through a completed challenge.",
                color=COLOR_TEXT_MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
        ]
        if others > 0:
            success_lines.append(
                ft.Text(
                    f"The challenge is now Solved. {others} other participant(s) "
                    f"will see it as solved.",
                    size=12,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        page.views[-1] = page_view(
            "/review",
            [
                app_bar("Review & Verify", "RATE_REVIEW"),
                ft.Container(
                    content=ft.Column(
                        controls=success_lines,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                ),
                back_button(go_business),
            ],
        )
        page.update()

    async def request_changes(e):
        feedback_field.visible = True
        submit_feedback_button.visible = True
        request_changes_button.visible = False
        page.update()

    feedback_field = ft.TextField(
        label="What needs improvement?", multiline=True, visible=False
    )

    async def submit_feedback(e):
        submission.request_changes(feedback_field.value or "")
        ds.save()
        refresh()

    submit_feedback_button = ft.Button(
        "Send feedback", on_click=submit_feedback, visible=False,
        icon=icon("SEND"), bgcolor=COLOR_SUCCESS, color="#FFFFFF",
    )
    request_changes_button = ft.Button(
        "Request changes", on_click=request_changes,
        icon=icon("CHAT_BUBBLE_OUTLINE"), bgcolor="#E8E3DC", color=COLOR_TEXT,
    )
    verify_button = ft.Button(
        "Verify skill", on_click=verify,
        icon=icon("CHECK_CIRCLE_OUTLINE"), bgcolor=COLOR_SUCCESS, color="#FFFFFF",
    )

    top_controls = [app_bar("Review & Verify", "RATE_REVIEW")]
    if len(ready) > 1:
        top_controls.append(
            ft.Text(
                f"{len(ready)} submissions waiting. Showing the oldest first.",
                size=12,
                color=COLOR_TEXT_MUTED,
            )
        )

    return page_view(
        "/review",
        top_controls
        + [
            card(ft.Column(controls=sections)),
            ft.Container(height=12),
            ft.Text("SKILL TRUST LEVEL", size=11, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.BOLD),
            trust_tracker(trust_before),
            ft.Container(height=16),
            feedback_field,
            ft.Row(controls=[request_changes_button, submit_feedback_button, verify_button]),
            back_button(go_business),
        ],
    )