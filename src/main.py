import os
import secrets
import flet as ft
from paths import INCOMING_DIR

from models.enums import Role
from pages.add_evidence import add_evidence_page
from pages.add_skill import add_skill_page
from pages.auth import access_denied_page, login_page, signup_page
from pages.business import business_page
from pages.challenges import challenges_page
from pages.passport import passport_page
from pages.post_challenge import post_challenge_page
from pages.review_verify import review_verify_page
from pages.welcome import welcome_page
from services.data_service import DataService
from theme import page_view, back_button, icon_text

PUBLIC_ROUTES = {"/", "/login", "/signup-youth", "/signup-business"}
YOUTH_ROUTES = {"/passport", "/challenges", "/add-evidence", "/add-skill"}
BUSINESS_ROUTES = {"/business", "/post-challenge", "/review"}


def main(page: ft.Page):
    page.title = "ProofPath"
    page.theme_mode = ft.ThemeMode.LIGHT

    data_service = DataService()

    # In Flet 1.0 the file picker is a "service": register it once, up front,
    # and share it with the pages that need it.
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def go_home(e):
        await page.push_route("/")

    def is_allowed(route: str) -> bool:
        """Route guard: public pages for everyone, youth pages for youth
        accounts, business pages for business accounts."""
        if route in PUBLIC_ROUTES:
            return True
        account = data_service.current_account
        if route in YOUTH_ROUTES:
            return account is not None and account.role == Role.YOUTH
        if route in BUSINESS_ROUTES:
            return account is not None and account.role == Role.BUSINESS
        return True  # unknown routes fall through to the 404 page

    def route_change():
        data_service.release_expired()
        page.views.clear()
        route = page.route

        if not is_allowed(route):
            page.views.append(access_denied_page(page, data_service))
        elif route == "/":
            page.views.append(welcome_page(page, data_service))
        elif route == "/login":
            page.views.append(login_page(page, data_service))
        elif route == "/signup-youth":
            page.views.append(signup_page(page, data_service, Role.YOUTH))
        elif route == "/signup-business":
            page.views.append(signup_page(page, data_service, Role.BUSINESS))
        elif route == "/passport":
            page.views.append(passport_page(page, data_service))
        elif route == "/add-skill":
            page.views.append(add_skill_page(page, data_service))
        elif route == "/challenges":
            page.views.append(challenges_page(page, data_service, file_picker))
        elif route == "/add-evidence":
            page.views.append(add_evidence_page(page, data_service))
        elif route == "/business":
            page.views.append(business_page(page, data_service))
        elif route == "/post-challenge":
            page.views.append(post_challenge_page(page, data_service))
        elif route == "/review":
            page.views.append(review_verify_page(page, data_service))
        else:
            page.views.append(
                page_view(
                    route,
                    [
                        icon_text("ERROR_OUTLINE", "Page not found", size=20,
                                  weight=ft.FontWeight.BOLD, center=True),
                        back_button(go_home),
                    ],
                    center=True,
                )
            )

        page.update()

    async def view_pop(e):
        if e.view is not None:
            page.views.remove(e.view)
            top_view = page.views[-1]
            await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    route_change()


if __name__ == "__main__":
    if os.getenv("PROOFPATH_WEB") == "1":
        # Flet refuses to create upload URLs without a signing key.
        os.environ.setdefault("FLET_SECRET_KEY", secrets.token_hex(32))
        INCOMING_DIR.mkdir(parents=True, exist_ok=True)
        ft.run(
            main,
            view=ft.AppView.WEB_BROWSER,
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
            upload_dir=str(INCOMING_DIR),
        )
    else:
        ft.run(main)