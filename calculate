import flet as ft
import requests
import re
import threading

def parse_player_page(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None, None

    html = response.text
    
    # Extract player's own rating
    try:
        player_rating_match = re.search(r"Рейтинг\s*</span></td><td[^>]*><b>(\d{4})", html)
        if not player_rating_match:
            player_rating_match = re.search(r"Rating\s*</span></td><td[^>]*><b>(\d{4})", html) # English version
        player_rating = int(player_rating_match.group(1))
    except (AttributeError, ValueError):
        return None, None
        
    games = []
    # Find the table with game results
    table_regex = r"<table class=CRs1_table>(.*?)</table>"
    table_match = re.search(table_regex, html, re.DOTALL)
    
    if not table_match:
        return player_rating, []

    table_html = table_match.group(1)
    
    # Regex to find rows and extract opponent rating and result
    row_regex = r"<tr>.*?<td[^>]*>(\d+)</td>.*?<td[^>]*>(\d{4})</td>.*?<td[^>]*>([01½])</td>.*?</tr>"
    rows = re.findall(row_regex, table_html, re.DOTALL)
    
    for row in rows:
        try:
            opponent_rating = int(row[1])
            result_str = row[2]
            
            if result_str == '1':
                result = 1.0
            elif result_str == '0':
                result = 0.0
            else: # '½'
                result = 0.5
                
            games.append({"opponent_rating": opponent_rating, "result": result})
        except (ValueError, IndexError):
            continue
            
    return player_rating, games

def calculate_new_rating(old_rating, games):
    """
    Calculates the new rating based on the provided games and a K-factor of 40.
    """
    k = 40
    total_expected_score = 0
    actual_score = 0
    
    for game in games:
        opponent_rating = game['opponent_rating']
        actual_score += game['result']
        
        # We = 1 / (1 + 10^((Ropp - Ro) / 400))
        expected_score = 1 / (1 + 10**((opponent_rating - old_rating) / 400))
        total_expected_score += expected_score
        
    rating_change = k * (actual_score - total_expected_score)
    
    return old_rating + round(rating_change)

def main(page: ft.Page):
    page.title = "Калькулятор рейтинга ФШР"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_height = 400
    page.padding = 30

    def calculate_clicked(e):
        url = url_input.value
        if not url:
            return

        progress_ring.visible = True
        calculate_button.disabled = True
        page.update()

        def do_calculation():
            old_rating, games = parse_player_page(url)
            
            def show_results(old, new, change):
                old_rating_text.value = f"Старый рейтинг: {old}"
                new_rating_text.value = f"Новый рейтинг: {new}"
                change_text.value = f"Изменение: {change:+.0f}"
                if change > 0:
                    change_text.color = ft.colors.GREEN_400
                elif change < 0:
                    change_text.color = ft.colors.RED_400
                else:
                    change_text.color = ft.colors.WHITE
            
            if old_rating is None:
                new_rating_text.value = "Ошибка: не удалось получить данные"
                old_rating_text.value = ""
                change_text.value = ""
            else:
                new_rating = calculate_new_rating(old_rating, games)
                change = new_rating - old_rating
                show_results(old_rating, new_rating, change)

            progress_ring.visible = False
            calculate_button.disabled = False
            page.update()

        threading.Thread(target=do_calculation).start()

    url_input = ft.TextField(
        label="URL страницы игрока на chess-results.com",
        width=550,
        border_radius=10,
    )

    calculate_button = ft.ElevatedButton(
        text="Рассчитать",
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
                url_input,
                ft.Row([calculate_button, progress_ring], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(height=20),
                results_container,
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    
    page.update()

ft.app(target=main)
