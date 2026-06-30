import requests
from bs4 import BeautifulSoup
import re


def parse_player_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=(5, 10))
        response.raise_for_status()
    except requests.RequestException:
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    player_rating = None
    games = []

    # --- Find player's rating ---
    # Look for <td> with exact text "Рейтинг" or "Rating" (not "Нац.рейтинг", "Междун. рейтинг")
    for td in soup.find_all('td'):
        text = td.get_text(strip=True)
        if text in ('Рейтинг', 'Rating'):
            next_td = td.find_next_sibling('td')
            if next_td:
                match = re.search(r'\b(\d{3,4})\b', next_td.get_text(strip=True))
                if match:
                    player_rating = int(match.group(1))
                    break

    if player_rating is None:
        return None, None

    # --- Find the game table by looking for column headers ---
    game_table = None
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        # Look for known chess-results column headers
        if 'Тур' in headers and 'Рейт.' in headers and 'Рез.' in headers:
            game_table = table
            break

    if game_table is None:
        return player_rating, games

    # --- Map column indices ---
    header_cells = game_table.find_all('th')
    col_index = {}
    for i, th in enumerate(header_cells):
        text = th.get_text(strip=True)
        if text == 'Рейт.':
            col_index['rating'] = i
        elif text == 'Рез.':
            col_index['result'] = i

    if 'rating' not in col_index or 'result' not in col_index:
        return player_rating, games

    # --- Parse game rows ---
    half_char = '\u00bd'  # ½
    for row in game_table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) <= max(col_index['rating'], col_index['result']):
            continue

        rating_text = cells[col_index['rating']].get_text(strip=True)
        result_text = cells[col_index['result']].get_text(strip=True)

        # Skip non-rating values (bye, empty, etc.)
        if not rating_text.isdigit() or len(rating_text) < 3:
            continue

        opponent_rating = int(rating_text)

        # Parse result
        result_val = None
        if result_text in ('1', '1.0'):
            result_val = 1.0
        elif result_text in ('0', '0.0'):
            result_val = 0.0
        elif result_text in (half_char, '1/2', '0.5'):
            result_val = 0.5
        else:
            # Skip unplayed games (empty, -, *, etc.)
            continue

        games.append({"opponent_rating": opponent_rating, "result": result_val})

    return player_rating, games


def calculate_new_rating(old_rating, games, k=40, limit_400=True):
    total_expected_score = 0
    actual_score = 0

    for game in games:
        opponent_rating = game['opponent_rating']
        actual_score += game['result']

        diff = opponent_rating - old_rating
        if limit_400:
            diff = max(min(diff, 400), -400)

        expected_score = 1 / (1 + 10 ** (diff / 400))
        total_expected_score += expected_score

    rating_change = k * (actual_score - total_expected_score)
    return old_rating + round(rating_change)
