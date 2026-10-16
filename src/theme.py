import flet as ft

from models.enums import TrustLevel

# South African-friendly, optimistic palette — avoid generic SaaS blue.
COLOR_PRIMARY = "#E85D2F"       # warm orange: primary actions, accents
COLOR_SUCCESS = "#1B8A5A"       # green: verified / solved
COLOR_WARNING = "#D99730"       # amber: evidence-backed / pending
COLOR_MUTED = "#8A8580"         # grey: self-declared, inactive
COLOR_BG = "#FAF6F1"            # warm off-white background
COLOR_CARD_BG = "#FFFFFF"
COLOR_TEXT = "#2B2420"          # near-black warm brown
COLOR_TEXT_MUTED = "#6B655F"
COLOR_ERROR = "#C0392B"


# ---------- icons ----------

def icon(name: str):
    """Look up a Material icon by name. Falls back to a plain dot if the
    name doesn't exist, so a wrong icon name can never crash the app."""
    return getattr(ft.Icons, name, ft.Icons.CIRCLE)


def icon_text(icon_name: str, text: str, size: int = 14, color: str = COLOR_TEXT,
              weight=None, center: bool = False) -> ft.Row:
    """An icon followed by text. center=True hugs the content and centres it
    (for titles); otherwise the text fills the row and wraps if long."""
    return ft.Row(
        controls=[
            ft.Icon(icon(icon_name), size=size + 2, color=color),
            ft.Text(text, size=size, color=color, weight=weight, expand=not center),
        ],
        spacing=6,
        tight=center,
        alignment=ft.MainAxisAlignment.CENTER if center else ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER if center else ft.CrossAxisAlignment.START,
    )


# ---------- badges ----------

def pill(text: str, bgcolor: str, color: str = "#FFFFFF", icon_name: str | None = None) -> ft.Container:
    """A small rounded label, optionally with an icon."""
    label = ft.Text(text, color=color, size=12, weight=ft.FontWeight.BOLD)
    if icon_name:
        content = ft.Row(
            controls=[ft.Icon(icon(icon_name), size=14, color=color), label],
            spacing=4,
            tight=True,
        )
    else:
        content = label
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=12,
    )


TRUST_BADGE = {
    TrustLevel.SELF_DECLARED: {"label": "○ Self-declared", "color": COLOR_MUTED},
    TrustLevel.EVIDENCE_BACKED: {"label": "◐ Evidence-backed", "color": COLOR_WARNING},
    TrustLevel.BUSINESS_VERIFIED: {"label": "✓ Business-verified", "color": COLOR_SUCCESS},
}


def trust_badge(trust_level: TrustLevel) -> ft.Container:
    """Pill for a skill's trust level, identical on every screen."""
    info = TRUST_BADGE[trust_level]
    return pill(info["label"], info["color"])


def challenge_badge(solved: bool) -> ft.Container:
    """Pending (still being worked on) or Solved (a solution was verified)."""
    if solved:
        return pill("Solved", COLOR_SUCCESS, icon_name="CHECK_CIRCLE")
    return pill("Pending", COLOR_WARNING, icon_name="HOURGLASS_EMPTY")


def accepted_counter(ch) -> ft.Row:
    """'3 of 5 accepted', turning amber with 'Full' once the limit is reached."""
    text = f"{ch.accepted_count} of {ch.max_participants} accepted"
    if ch.is_full and not ch.is_solved:
        return icon_text("GROUPS", f"{text} · Full", size=12,
                         color=COLOR_WARNING, weight=ft.FontWeight.BOLD)
    return icon_text("GROUPS", text, size=12, color=COLOR_TEXT_MUTED)

# ---------- layout pieces ----------

def card(content: ft.Control) -> ft.Container:
    """Rounded white card for list items."""
    return ft.Container(
        content=content,
        bgcolor=COLOR_CARD_BG,
        padding=16,
        border_radius=12,
        margin=ft.Margin.only(bottom=10),
    )


def divider() -> ft.Container:
    return ft.Container(
        height=1,
        bgcolor="#E8E3DC",
        margin=ft.Margin.only(top=12, bottom=12),
    )


def info_section(label: str, content: ft.Control, tint: str | None = None,
                 icon_name: str | None = None) -> ft.Container:
    """A labelled block: small uppercase caption above its content.
    Pass tint for a soft coloured background, icon_name for a caption icon."""
    if icon_name:
        caption = icon_text(icon_name, label, size=11, color=COLOR_TEXT_MUTED,
                            weight=ft.FontWeight.BOLD)
    else:
        caption = ft.Text(label, size=11, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.BOLD)
    return ft.Container(
        content=ft.Column(controls=[caption, content], spacing=4),
        bgcolor=tint,
        padding=12 if tint else 0,
        border_radius=10,
    )


def avatar(name: str, size: int = 44) -> ft.Container:
    """Circle with the person's initials."""
    initials = "".join(w[0] for w in name.split()[:2]).upper()
    return ft.Container(
        content=ft.Text(initials, color="#FFFFFF", weight=ft.FontWeight.BOLD),
        bgcolor=COLOR_PRIMARY,
        width=size,
        height=size,
        border_radius=size // 2,
        alignment=ft.Alignment.CENTER,
    )


def stat_strip(stats: list[tuple[str, str, str]]) -> ft.Container:
    """Dark summary bar. Pass [(value, label, icon_name), ...]."""
    columns = [
        ft.Column(
            controls=[
                ft.Icon(icon(icon_name), size=20, color="#FFFFFF"),
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ft.Text(label, size=12, color="#FFFFFF"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
        )
        for value, label, icon_name in stats
    ]
    return ft.Container(
        content=ft.Row(controls=columns, alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        bgcolor="#2B2420",
        padding=16,
        border_radius=12,
        margin=ft.Margin.only(bottom=16),
    )


def trust_tracker(current_level: TrustLevel) -> ft.Row:
    """Labelled ○ ◐ ✓ progression, with the current level highlighted."""
    levels = [
        TrustLevel.SELF_DECLARED,
        TrustLevel.EVIDENCE_BACKED,
        TrustLevel.BUSINESS_VERIFIED,
    ]
    dots = []
    for i, level in enumerate(levels):
        info = TRUST_BADGE[level]
        is_current = level == current_level
        dots.append(
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            info["label"].split(" ")[0],  # just the glyph
                            size=16,
                            color="#FFFFFF" if is_current else COLOR_MUTED,
                        ),
                        bgcolor=info["color"] if is_current else "#E8E3DC",
                        width=36,
                        height=36,
                        border_radius=18,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Text(
                        info["label"].split(" ", 1)[1],
                        size=10,
                        color=COLOR_TEXT if is_current else COLOR_TEXT_MUTED,
                        weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        if i < len(levels) - 1:
            dots.append(ft.Container(width=24, height=2, bgcolor="#E8E3DC"))
    return ft.Row(controls=dots, alignment=ft.MainAxisAlignment.CENTER)


# ---------- buttons ----------

def primary_button(text: str, on_click, icon_name: str | None = None) -> ft.Button:
    return ft.Button(
        text,
        on_click=on_click,
        icon=icon(icon_name) if icon_name else None,
        bgcolor=COLOR_PRIMARY,
        color="#FFFFFF",
    )


def secondary_button(text: str, on_click, icon_name: str | None = None) -> ft.Button:
    return ft.Button(
        text,
        on_click=on_click,
        icon=icon(icon_name) if icon_name else None,
        bgcolor="#E8E3DC",
        color=COLOR_TEXT,
    )


def back_button(on_click) -> ft.TextButton:
    return ft.TextButton(
        "Back",
        on_click=on_click,
        icon=icon("ARROW_BACK"),
        style=ft.ButtonStyle(color=COLOR_TEXT),
    )


# ---------- page scaffolding ----------

def app_bar(title: str, icon_name: str | None = None) -> ft.AppBar:
    """Top bar with a centred title (and optional icon), same on every page."""
    parts = []
    if icon_name:
        parts.append(ft.Icon(icon(icon_name), size=22, color="#FFFFFF"))
    parts.append(ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF"))
    return ft.AppBar(
        title=ft.Row(
            controls=parts,
            spacing=8,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        center_title=True,
        bgcolor=COLOR_PRIMARY,
    )


def page_view(route: str, controls: list, center: bool = False) -> ft.View:
    """Every screen goes through here: same background, and every page
    scrolls when its content is taller than the window."""
    extra = {}
    if center:
        extra["horizontal_alignment"] = ft.CrossAxisAlignment.CENTER
    return ft.View(
        route=route,
        bgcolor=COLOR_BG,
        scroll=ft.ScrollMode.AUTO,
        controls=controls,
        **extra,
    )

# ---------- helpers ----------
def format_remaining(td) -> str:
    """timedelta -> '9d 4h', '5h 12m', '42m'."""
    seconds = max(int(td.total_seconds()), 0)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m"
    return "under a minute"


def format_hours(hours: int) -> str:
    """24 -> '24 hours', 72 -> '3 days'."""
    if hours >= 48 and hours % 24 == 0:
        return f"{hours // 24} days"
    return f"{hours} hours"