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

    # --- State ---
    game_cards_list = []
    current_card_index = 0
    total_games = 0
    _drag_start_x = 0

    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_toggle.icon = ft.Icons.DARK_MODE
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_toggle.icon = ft.Icons.LIGHT_MODE
        page.update()

    def clear_url(e):
        nonlocal game_cards_list, current_card_index, total_games
        url_input.value = ""
        url_input.focus()
        result_card.visible = False
        games_section.visible = False
        error_text.visible = False
        page.update()

    def on_k_change(e):
        k_description.value = K_OPTIONS[k_factor_dropdown.value]
        page.update()

    def go_to_card(index):
        nonlocal current_card_index
        if 0 <= index < total_games:
            current_card_index = index
            cards_switcher.content = game_cards_list[current_card_index]
            card_counter.value = f"{current_card_index + 1} / {total_games}"
            prev_button.disabled = current_card_index == 0
            next_button.disabled = current_card_index == total_games - 1
            page.update()

    def prev_card(e):
        go_to_card(current_card_index - 1)

    def next_card(e):
        go_to_card(current_card_index + 1)

    def build_single_game_card(game, expected, round_num):
        if expected is not None:
            rounded = round(expected * 2) / 2
            if rounded == int(rounded):
                exp_str = str(int(rounded))
            else:
                exp_str = "\u00bd"
        else:
            exp_str = "-"

        is_bye = game.get('is_bye', False)

        if is_bye:
            return ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=16,
                padding=ft.Padding(30, 40, 30, 40),
                width=300,
                height=360,
                content=ft.Column(
                    [
                        ft.Text(f"Тур {round_num}", size=14, color=ft.Colors.GREY_500),
                        ft.Container(height=18),
                        ft.Text("BYE", size=26, weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(height=12),
                        ft.Text("Свободный тур", size=15, color=ft.Colors.GREY_400,
                                text_align=ft.TextAlign.CENTER),
                        ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                        ft.Container(height=18),
                        ft.Text("1", size=56, color=ft.Colors.GREEN_400,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
            )

        if game.get('is_forfeit'):
            forfeit_label = "Техническая победа" if game['result'] == 1.0 else "Техническое поражение"
            fcolor = ft.Colors.GREEN_400 if game['result'] == 1.0 else ft.Colors.RED_400
            result_display = "1" if game['result'] == 1.0 else "0"
            return ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=16,
                padding=ft.Padding(30, 40, 30, 40),
                width=300,
                height=360,
                content=ft.Column(
                    [
                        ft.Text(f"Тур {round_num}", size=14, color=ft.Colors.GREY_500),
                        ft.Container(height=18),
                        ft.Text(
                            game.get('opponent_name', ''),
                            size=26, weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=12),
                        ft.Text(
                            f"Рейт: {game['opponent_rating']}  \u00b7  {forfeit_label}",
                            size=15, color=ft.Colors.GREY_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                        ft.Container(height=18),
                        ft.Text(result_display, size=56, color=fcolor,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
            )

        if game['result'] == 1.0:
            result_text = "1"
            result_color = ft.Colors.GREEN_400
        elif game['result'] == 0.0:
            result_text = "0"
            result_color = ft.Colors.RED_400
        else:
            result_text = "\u00bd"
            result_color = ft.Colors.GREY_300

        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=16,
            padding=ft.Padding(30, 40, 30, 40),
            width=300,
            height=360,
            content=ft.Column(
                [
                    ft.Text(f"Тур {round_num}", size=14, color=ft.Colors.GREY_500),
                    ft.Container(height=18),
                    ft.Text(
                        game.get('opponent_name', ''),
                        size=26,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=12),
                    ft.Text(
                        f"Рейт: {game['opponent_rating']}  \u00b7  Ожид: {exp_str}",
                        size=15,
                        color=ft.Colors.GREY_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    ft.Container(height=18),
                    ft.Text(
                        result_text,
                        size=56,
                        color=result_color,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
        )

    def on_drag_start(e):
        nonlocal _drag_start_x
        _drag_start_x = e.local_position.x

    def on_drag_end(e):
        nonlocal current_card_index
        dx = e.local_position.x - _drag_start_x
        if dx > 50 and current_card_index > 0:
            go_to_card(current_card_index - 1)
        elif dx < -50 and current_card_index < total_games - 1:
            go_to_card(current_card_index + 1)

    def calculate_clicked(e):
        nonlocal game_cards_list, current_card_index, total_games

        url = url_input.value
        if not url:
            return

        progress_ring.visible = True
        calculate_button.disabled = True
        result_card.visible = False
        games_section.visible = False
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
                new_rating, actual_score, expected_score, game_expected = (
                    calculate_new_rating(old_rating, games, k=k)
                )
                change = new_rating - old_rating

                card_old_rating.value = str(old_rating)
                card_new_rating.value = str(new_rating)
                card_change.value = f"{change:+.0f}"
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

                total_games = len(games)
                bye_count = sum(1 for g in games if g.get('is_bye'))
                normal_games = total_games - bye_count
                games_str = f"{normal_games} игр"
                if bye_count:
                    games_str += f" ({bye_count} bye)"
                card_stats.value = (
                    f"{games_str} \u00b7 K={k} \u00b7 "
                    f"Ожидал: {expected_score} \u00b7 Набрал: {actual_score}"
                )
                current_card_index = 0
                game_cards_list = [
                    build_single_game_card(g, exp, i + 1)
                    for i, (g, exp) in enumerate(zip(games, game_expected))
                ]

                cards_switcher.content = game_cards_list[0]
                card_counter.value = f"1 / {total_games}"
                prev_button.disabled = True
                next_button.disabled = total_games <= 1
                games_section.visible = True

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
        dense=True,
        suffix=ft.IconButton(
            icon=ft.Icons.CLOSE,
            tooltip="Очистить",
            on_click=clear_url,
        ),
    )

    k_factor_dropdown = ft.Dropdown(
        width=110,
        height=48,
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
        padding=ft.Padding(25, 25, 25, 25),
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

    # ------------------- Flash Card Section -------------------

    prev_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        icon_size=28,
        disabled=True,
        on_click=prev_card,
    )

    card_counter = ft.Text("", size=14, color=ft.Colors.GREY_400)

    next_button = ft.IconButton(
        icon=ft.Icons.ARROW_FORWARD,
        icon_size=28,
        disabled=True,
        on_click=next_card,
    )

    cards_switcher = ft.AnimatedSwitcher(
        content=ft.Container(),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=300,
    )

    swipe_wrapper = ft.GestureDetector(
        content=cards_switcher,
        on_horizontal_drag_start=on_drag_start,
        on_horizontal_drag_end=on_drag_end,
    )

    games_section = ft.Container(
        visible=False,
        content=ft.Column(
            [
                swipe_wrapper,
                ft.Container(height=12),
                ft.Row(
                    [prev_button, card_counter, next_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=15,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
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
                        games_section,
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
