import flet as ft
import requests
from bs4 import BeautifulSoup
import re

def parse_player_page(url):
    try:
        # Set User-Agent to bypass basic bot protections
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=(5, 10))
        response.raise_for_status()
    except requests.RequestException:
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    player_rating = None
    games = []

    # PART 1: Find the player's own Elo rating dynamically
    for td in soup.find_all('td'):
        if 'Рейтинг' in td.text or 'Rating' in td.text:
            next_td = td.find_next_sibling('td')
            if next_td:
                match = re.search(r'\b(\d{4})\b', next_td.text)
                if match:
                    player_rating = int(match.group(1))
                    break

    if player_rating is None:
        return None, None

    # PART 2: Find the match table independently of class names by scanning all rows
    for row in soup.find_all('tr'):
        cols = [col.text.strip() for col in row.find_all('td')]
        
        # A valid match row should have at least 4 cells
        if len(cols) < 4:
            continue
            
        opponent_rating = None
        result_val = None
        
        for text in cols:
            # Clean up non-breaking spaces and whitespace
            clean_text = text.replace('\xa0', '').strip()
            
            # Look for a 4-digit opponent rating
            if len(clean_text) == 4 and clean_text.isdigit():
                opponent_rating = int(clean_text)
            # Look for the match result covering various formats
            elif clean_text in ['1', '0', '½', '1/2', '0.5']:
                if clean_text == '1': result_val = 1.0
                elif clean_text == '0': result_val = 0.0
                else: result_val = 0.5
                
        # If both opponent rating and result are found in the same row, it's a valid match record
        if opponent_rating is not None and result_val is not None:
            games.append({"opponent_rating": opponent_rating, "result": result_val})

    return player_rating, games

def calculate_new_rating(old_rating, games):
    """Calculates the new rating with a static K-factor."""
    k = 40  # Kept static as requested
    total_expected_score = 0
    actual_score = 0
    
    for game in games:
        opponent_rating = game['opponent_rating']
        actual_score += game['result']
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

        # Show the loading ring and disable the button
        progress_ring.visible = True
        calculate_button.disabled = True
        old_rating_text.value = ""
        new_rating_text.value = ""
        change_text.value = ""
        page.update()

        try:
            old_rating, games = parse_player_page(url)
            
            if old_rating is None:
                new_rating_text.value = "Ошибка: не удалось получить данные"
            elif len(games) == 0:
                old_rating_text.value = f"Старый рейтинг: {old_rating}"
                new_rating_text.value = "Ошибка: Партии не найдены"
            else:
                new_rating = calculate_new_rating(old_rating, games)
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
            # Hide the loading ring when the process is done
            progress_ring.visible = False
            calculate_button.disabled = False
            page.update()

    url_input = ft.TextField(
        label="URL страницы игрока на chess-results.com",
        width=550,
        border_radius=10,
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
