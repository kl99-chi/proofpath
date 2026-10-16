import flet as ft

from pages.welcome import welcome_page
from pages.passport import passport_page
from pages.business import business_page
from pages.challenges import challenges_page
from pages.review_verify import review_verify_page
from pages.add_evidence import add_evidence_page
from pages.post_challenge import post_challenge_page
from theme import page_view, back_button, icon_text
from services.data_service import DataService


def main(page: ft.Page):
    page.title = "ProofPath"
    page.theme_mode = ft.ThemeMode.LIGHT

    data_service = DataService()
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def go_home(e):
        await page.push_route("/")

    def route_change():
        data_service.release_expired()
        page.views.clear()

        if page.route == "/":
            page.views.append(welcome_page(page, data_service))
        elif page.route == "/passport":
            page.views.append(passport_page(page, data_service))
        elif page.route == "/business":
            page.views.append(business_page(page, data_service))
        elif page.route == "/challenges":
            page.views.append(challenges_page(page, data_service, file_picker))
        elif page.route == "/review":
            page.views.append(review_verify_page(page, data_service))
        elif page.route == "/add-evidence":
            page.views.append(add_evidence_page(page, data_service))    
        elif page.route == "/post-challenge":
            page.views.append(post_challenge_page(page, data_service))
        else:
            page.views.append(
                page_view(
                    page.route,
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


ft.run(main)