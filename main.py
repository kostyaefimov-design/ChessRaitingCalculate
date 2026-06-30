import flet as ft
from backend import parse_player_page, calculate_new_rating

K_OPTIONS = {
    "40": "Новые игроки (< 30 партий, рейтинг < 2400) и юниоры (< 18 лет, < 2300)",
    "20": "Игроки с рейтингом < 2400 (рапид, блиц)",
    "10": "Игроки, достигавшие рейтинга 2400+",
}


def main(page: ft.Page):
    page.title = "Калькулятор рейтинга ФШР"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_height = 520
    page.padding = 30

    def clear_url(e):
        url_input.value = ""
        url_input.focus()
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
        old_rating_text.value = ""
        new_rating_text.value = ""
        change_text.value = ""
        page.update()

        try:
            old_rating, games = parse_player_page(url)
            k = int(k_factor_dropdown.value)

            if old_rating is None:
                new_rating_text.value = "Ошибка: не удалось получить данные"
            elif len(games) == 0:
                old_rating_text.value = f"Старый рейтинг: {old_rating}"
                new_rating_text.value = "Ошибка: Партии не найдены"
            else:
                new_rating = calculate_new_rating(old_rating, games, k=k)
                change = new_rating - old_rating

                old_rating_text.value = f"Старый рейтинг: {old_rating} | Количество игр: {len(games)}"
                new_rating_text.value = f"Новый рейтинг: {new_rating}"
                change_text.value = f"Изменение: {change:+.0f}"

                if change > 0:
                    change_text.color = ft.Colors.GREEN_400
                elif change < 0:
                    change_text.color = ft.Colors.RED_400
                else:
                    change_text.color = ft.Colors.WHITE
        except Exception as ex:
            new_rating_text.value = f"Системная ошибка: {ex}"
        finally:
            progress_ring.visible = False
            calculate_button.disabled = False
            page.update()

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
            ft.dropdown.Option(key=k, text=f"K={k}")
            for k in K_OPTIONS
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
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    progress_ring = ft.ProgressRing(visible=False, width=24, height=24)

    old_rating_text = ft.Text(size=18)
    new_rating_text = ft.Text(size=22, weight=ft.FontWeight.BOLD)
    change_text = ft.Text(size=18)

    results_container = ft.Column(
        controls=[
            old_rating_text,
            new_rating_text,
            change_text,
        ],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.add(
        ft.Column(
            [
                ft.Text("Калькулятор рейтинга ФШР", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Вставьте ссылку на страницу с результатами игрока", size=16),
                ft.Row([url_input, k_factor_dropdown], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                k_description,
                ft.Row([calculate_button, progress_ring], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(height=20),
                results_container,
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
