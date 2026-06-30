import flet as ft
from backend import parse_player_page, calculate_new_rating

K_OPTIONS = {
    "40": "Новые игроки (< 30 партий, рейтинг < 2400) и юниоры (< 18 лет, < 2300)",
    "20": "Игроки с рейтингом < 2400 (рапид, блиц)",
    "10": "Игроки, достигавшие рейтинга 2400+",
}


def main(page: ft.Page):
    page.title = "Калькулятор рейтинга ФШР"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_height = 580
    page.padding = 30
    page.scroll = ft.ScrollMode.AUTO

    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_toggle.icon = ft.Icons.DARK_MODE
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_toggle.icon = ft.Icons.LIGHT_MODE
        page.update()

    def clear_url(e):
        url_input.value = ""
        url_input.focus()
        result_card.visible = False
        error_text.visible = False
        page.update()

    def on_k_change(e):
        k_description.value = K_OPTIONS[k_factor_dropdown.value]
        page.update()

    def calculate_clicked(e):
        url = url_input.value
        if not url:
            return

        progress_ring.visible = True
        calculate_button.disabled = True
        result_card.visible = False
        error_text.visible = False
        page.update()

        try:
            old_rating, games = parse_player_page(url)
            k = int(k_factor_dropdown.value)

            if old_rating is None:
                error_text.value = "Ошибка: не удалось получить данные"
                error_text.visible = True
            elif len(games) == 0:
                error_text.value = "Ошибка: Партии не найдены"
                error_text.visible = True
            else:
                new_rating, actual_score, expected_score = calculate_new_rating(
                    old_rating, games, k=k
                )
                change = new_rating - old_rating

                card_old_rating.value = str(old_rating)
                card_new_rating.value = str(new_rating)
                card_change.value = f"{change:+.0f}"
                card_stats.value = (
                    f"{len(games)} игр \u00b7 K={k} \u00b7 "
                    f"Ожидал: {expected_score} \u00b7 Набрал: {actual_score}"
                )

                if change > 0:
                    card_trend_icon.icon = ft.Icons.TRENDING_UP
                    card_trend_icon.color = ft.Colors.GREEN_400
                    card_change.color = ft.Colors.GREEN_400
                elif change < 0:
                    card_trend_icon.icon = ft.Icons.TRENDING_DOWN
                    card_trend_icon.color = ft.Colors.RED_400
                    card_change.color = ft.Colors.RED_400
                else:
                    card_trend_icon.icon = ft.Icons.TRENDING_FLAT
                    card_trend_icon.color = ft.Colors.GREY_400
                    card_change.color = ft.Colors.GREY_400

                result_card.visible = True
        except Exception as ex:
            error_text.value = f"Системная ошибка: {ex}"
            error_text.visible = True
        finally:
            progress_ring.visible = False
            calculate_button.disabled = False
            page.update()

    # ------------------- UI Components -------------------

    theme_toggle = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE,
        icon_size=22,
        tooltip="Сменить тему",
        on_click=toggle_theme,
        top=5,
        right=5,
    )

    url_input = ft.TextField(
        label="URL страницы игрока на chess-results.com",
        expand=True,
        border_radius=10,
        suffix=ft.IconButton(
            icon=ft.Icons.CLOSE,
            tooltip="Очистить",
            on_click=clear_url,
        ),
    )

    k_factor_dropdown = ft.Dropdown(
        width=110,
        value="40",
        options=[
            ft.dropdown.Option(key=k, text=f"K={k}") for k in K_OPTIONS
        ],
        on_select=on_k_change,
    )

    k_description = ft.Text(
        K_OPTIONS["40"],
        size=12,
        italic=True,
        color=ft.Colors.GREY_400,
    )

    calculate_button = ft.ElevatedButton(
        content=ft.Text("Рассчитать"),
        width=200,
        height=50,
        on_click=calculate_clicked,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    progress_ring = ft.ProgressRing(visible=False, width=24, height=24)

    error_text = ft.Text("", size=16, color=ft.Colors.RED_400, visible=False)

    # ------------------- Result Card -------------------

    card_old_rating = ft.Text("", size=44, weight=ft.FontWeight.BOLD)
    card_old_label = ft.Text("Старый", size=12, color=ft.Colors.GREY_500)

    card_trend_icon = ft.Icon(icon=ft.Icons.TRENDING_FLAT, size=38)

    card_new_rating = ft.Text("", size=44, weight=ft.FontWeight.BOLD)
    card_new_label = ft.Text("Новый", size=12, color=ft.Colors.GREY_500)

    card_change = ft.Text("", size=26)

    card_stats = ft.Text("", size=14, color=ft.Colors.GREY_400)

    result_card = ft.Container(
        visible=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=16,
        padding=ft.padding.all(25),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [card_old_rating, card_old_label],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                        card_trend_icon,
                        ft.Column(
                            [card_new_rating, card_new_label],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                card_change,
                card_stats,
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # ------------------- Page Layout -------------------

    page.add(
        ft.Stack(
            [
                ft.Column(
                    [
                        ft.Text(
                            "Калькулятор рейтинга ФШР",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "Вставьте ссылку на страницу с результатами игрока",
                            size=16,
                        ),
                        ft.Row(
                            [url_input, k_factor_dropdown],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        k_description,
                        ft.Row(
                            [calculate_button, progress_ring],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Divider(height=20),
                        result_card,
                        error_text,
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                theme_toggle,
            ],
        ),
    )


if __name__ == "__main__":
    ft.app(target=main)
