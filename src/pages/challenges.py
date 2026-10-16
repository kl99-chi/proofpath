import flet as ft

from models.enums import SubmissionStatus
from models.submission import Submission
from theme import (
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_WARNING, COLOR_SUCCESS, COLOR_ERROR,
    challenge_badge, accepted_counter, primary_button, secondary_button, card,
    back_button, page_view, app_bar, icon_text, format_remaining, format_hours,
)

CURRENT_YOUTH_ID = "Y001"


def challenges_page(page: ft.Page, ds, file_picker=None) -> ft.View:
    async def go_passport(e):
        await page.push_route("/passport")

    def refresh():
        page.views[-1] = challenges_page(page, ds, file_picker)
        page.update()

    def build_attachment_picker():
        """Returns (picked, control). `picked` is a dict the submit handler
        reads. control is None when uploads aren't switched on."""
        picked = {"path": None, "name": None}
        if file_picker is None:
            return picked, None

        label = ft.Text("No file attached", size=12, color=COLOR_TEXT_MUTED)

        async def choose(e):
            files = await file_picker.pick_files(allow_multiple=False)
            if not files:
                return  # dialog was cancelled
            chosen = files[0]
            if not chosen.path:
                label.value = "Couldn't read that file's location (desktop app only)."
                label.color = COLOR_ERROR
                page.update()
                return
            picked["path"] = chosen.path
            picked["name"] = chosen.name
            label.value = f"Attached: {chosen.name}"
            label.color = COLOR_SUCCESS
            page.update()

        control = ft.Row(
            controls=[secondary_button("Attach file", choose, "ATTACH_FILE"), label],
            wrap=True,
        )
        return picked, control

    def create_submission(challenge_id, note_field, picked, attempt_number=1):
        """Build, store and record a new Submission. Returns an error
        message, or None on success."""
        note = (note_field.value or "").strip()
        challenge = ds.challenges[challenge_id]
        if challenge.is_solved:
            return "This challenge was just solved, so it's closed to new submissions."
        if CURRENT_YOUTH_ID not in challenge.participants:
            return "You're no longer on this challenge."
        if attempt_number == 1:  # revisions after feedback aren't time-limited
            left = challenge.time_left(CURRENT_YOUTH_ID)
            if left is not None and left.total_seconds() <= 0:
                return (
                    "Your time limit has passed, so a first submission can't "
                    "be accepted. Go back and reopen the page."
                )

        new_id = f"SUB{len(ds.submissions) + 1:03d}"
        attachment_name, attachment_file = "", ""
        if picked["path"]:
            try:
                attachment_name, attachment_file = ds.store_attachment(
                    picked["path"], new_id
                )
            except OSError as ex:
                return f"Couldn't save the file: {ex}"

        submission = Submission(
            id=new_id,
            challenge_id=challenge_id,
            youth_id=CURRENT_YOUTH_ID,
            note=note,
            attempt_number=attempt_number,
            attachment_name=attachment_name,
            attachment_file=attachment_file,
        )
        ds.submissions[submission.id] = submission
        return None

    def countdown_line(ch):
        """How long this youth has left to submit, or None if their accept
        pre-dates time limits."""
        left = ch.time_left(CURRENT_YOUTH_ID)
        if left is None:
            return None
        if left.total_seconds() <= 0:
            return icon_text(
                "TIMER_OFF", "Time limit passed. Your spot is about to be released.",
                size=12, color=COLOR_ERROR, weight=ft.FontWeight.BOLD,
            )
        urgent = left < ch.time_limit / 4
        return icon_text(
            "TIMER", f"Submit within {format_remaining(left)}", size=12,
            color=COLOR_ERROR if urgent else COLOR_TEXT_MUTED,
            weight=ft.FontWeight.BOLD if urgent else None,
        )

    def build_card(ch):
        business = ds.businesses[ch.business_id]
        mine = ds.submissions_for(ch.id, CURRENT_YOUTH_ID)
        latest = mine[-1] if mine else None
        accepted_by_me = CURRENT_YOUTH_ID in ch.participants

        header = ft.Text(ch.title, weight=ft.FontWeight.BOLD, size=16, color=COLOR_TEXT)
        meta = ft.Text(
            f"{business.name} · Skill: {ch.skill_name} · Est. {ch.estimated_effort}",
            size=12,
            color=COLOR_TEXT_MUTED,
        )
        top = [
            ft.Row(
                controls=[header, challenge_badge(ch.is_solved)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            meta,
            accepted_counter(ch),
        ]

        # ---- solved: nothing left to do ----
        if ch.is_solved:
            if latest is not None and latest.status == SubmissionStatus.VERIFIED:
                top.append(
                    icon_text("VERIFIED", "You solved this challenge",
                              color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD)
                )
            elif accepted_by_me:
                top.append(
                    icon_text("INFO_OUTLINE", "Solved by another participant",
                              color=COLOR_TEXT_MUTED)
                )
            return card(ft.Column(controls=top))

        # ---- pending, and I haven't accepted it ----
        if not accepted_by_me:
            if ch.is_full:
                top.append(
                    icon_text("BLOCK", "This challenge is full. Pick another one.",
                              color=COLOR_WARNING, weight=ft.FontWeight.BOLD)
                )
                return card(ft.Column(controls=top))

            async def accept(e, challenge_id=ch.id):
                try:
                    ds.challenges[challenge_id].accept(CURRENT_YOUTH_ID)
                    ds.save()
                except ValueError:
                    # Someone took the last spot, or it was just solved.
                    # Refreshing below shows the current state.
                    pass
                refresh()

            limit_line = icon_text(
                "TIMER", f"Time limit: {format_hours(ch.time_limit_hours)} after accepting",
                size=12, color=COLOR_TEXT_MUTED,
            )
            rule_line = icon_text(
                "INFO_OUTLINE", "The first verified solution closes this challenge.",
                size=12, color=COLOR_TEXT_MUTED,
            )

            return card(
                ft.Column(
                    controls=top + [
                        limit_line,
                        primary_button("Accept challenge", accept, "CHECK_CIRCLE_OUTLINE"),
                    ]
                )
            )

        # ---- I accepted it, nothing submitted yet ----
        if latest is None:
            note_field = ft.TextField(label="What did you complete?", multiline=True)
            picked, attach_row = build_attachment_picker()
            error_text = ft.Text("", color=COLOR_ERROR, size=12)
            hint = ft.Text("", size=12, color=COLOR_WARNING)
            state = {"armed": False}

            async def submit(e, challenge_id=ch.id, field=note_field, picked=picked, err=error_text):
                problem = create_submission(challenge_id, field, picked)
                if problem:
                    err.value = problem
                    page.update()
                    return
                ds.save()
                refresh()

            async def withdraw(e, challenge_id=ch.id, hint=hint, state=state):
                if not state["armed"]:
                    # First tap only arms it, so a slip doesn't cost a spot.
                    state["armed"] = True
                    hint.value = "Tap Withdraw again to confirm. You'll give up your spot."
                    page.update()
                    return
                try:
                    ds.withdraw_participant(challenge_id, CURRENT_YOUTH_ID)
                except ValueError:
                    pass  # e.g. already submitted; the refresh shows the truth
                refresh()

            controls = top[:]
            line = countdown_line(ch)
            if line is not None:
                controls.append(line)
            controls.append(note_field)
            if attach_row is not None:
                controls.append(attach_row)
            controls += [
                error_text,
                hint,
                ft.Row(
                    controls=[
                        primary_button("Submit for verification", submit, "SEND"),
                        secondary_button("Withdraw", withdraw, "LOGOUT"),
                    ],
                    wrap=True,
                ),
            ]
            return card(ft.Column(controls=controls))

        # ---- the business asked for changes ----
        if latest.status == SubmissionStatus.CHANGES_REQUESTED:
            note_field = ft.TextField(label="Revise your submission", multiline=True)
            picked, attach_row = build_attachment_picker()
            error_text = ft.Text("", color=COLOR_ERROR, size=12)

            async def resubmit(e, challenge_id=ch.id, field=note_field, picked=picked,
                               err=error_text, prev=latest):
                problem = create_submission(
                    challenge_id, field, picked,
                    attempt_number=prev.attempt_number + 1,
                )
                if problem:
                    err.value = problem
                    page.update()
                    return
                ds.save()
                refresh()

            controls = top + [
                icon_text("CHAT_BUBBLE_OUTLINE", f"Changes requested: {latest.feedback}",
                          color=COLOR_WARNING, weight=ft.FontWeight.BOLD),
                note_field,
            ]
            if attach_row is not None:
                controls.append(attach_row)
            controls += [error_text, primary_button("Submit revised work", resubmit, "SEND")]
            return card(ft.Column(controls=controls))

        # ---- submitted, waiting on the business ----
        waiting = top + [
            icon_text("HOURGLASS_EMPTY", f"Awaiting verification from {business.name}",
                      color=COLOR_SUCCESS)
        ]
        if latest.has_attachment:
            waiting.append(
                icon_text("ATTACH_FILE", f"Attached: {latest.attachment_name}",
                          size=12, color=COLOR_TEXT_MUTED)
            )
        return card(ft.Column(controls=waiting))

    def closed_to_me(c):
        """Full, and I'm not one of the participants: I can't join it."""
        return c.is_full and CURRENT_YOUTH_ID not in c.participants

    # Available first, then full, then solved.
    ordered = sorted(
        ds.challenges.values(),
        key=lambda c: (c.is_solved, closed_to_me(c)),
    )
    solved = sum(1 for c in ordered if c.is_solved)
    full = sum(1 for c in ordered if not c.is_solved and closed_to_me(c))
    available = len(ordered) - solved - full

    # One-time messages, e.g. "you were withdrawn from X".
    notice_banners = [
        ft.Container(
            content=icon_text("INFO_OUTLINE", message, size=13, color=COLOR_TEXT),
            bgcolor="#FFF4E0",
            padding=12,
            border_radius=10,
        )
        for message in ds.pop_notices(CURRENT_YOUTH_ID)
    ]

    return page_view(
        "/challenges",
        [
            app_bar("Micro-Challenges", "FLAG"),
            ft.Text(
                "Small, scoped tasks that help you build real-world proof.",
                size=12,
                color=COLOR_TEXT_MUTED,
            ),
        ]
        + notice_banners
        + [
            ft.Text(f"{available} available · {full} full · {solved} solved",
                    weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            ft.Column(controls=[build_card(c) for c in ordered]),
            back_button(go_passport),
        ],
    )