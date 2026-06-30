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

    game_table = None
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if 'Тур' in headers and 'Рейт.' in headers and 'Рез.' in headers:
            game_table = table
            break

    if game_table is None:
        return player_rating, games

    header_cells = game_table.find_all('th')
    col_index = {}
    for i, th in enumerate(header_cells):
        text = th.get_text(strip=True)
        if text == 'Рейт.':
            col_index['rating'] = i
        elif text == 'Рез.':
            col_index['result'] = i
        elif text == 'Имя':
            col_index['name'] = i

    if 'rating' not in col_index or 'result' not in col_index:
        return player_rating, games

    half_char = '\u00bd'
    for row in game_table.find_all('tr'):
        cells = row.find_all('td')
        min_required = max(col_index.values())
        if len(cells) <= min_required:
            continue

        rating_text = cells[col_index['rating']].get_text(strip=True)
        result_text = cells[col_index['result']].get_text(strip=True)
        name_text = cells[col_index.get('name', 0)].get_text(strip=True) if 'name' in col_index else ""

        # Check for bye
        bye_keywords = ['bye', 'freilos', 'входной']
        if (not rating_text.isdigit() or len(rating_text) < 3) and any(kw in name_text.lower() for kw in bye_keywords):
            games.append({
                "opponent_rating": None,
                "result": 1.0,
                "opponent_name": "BYE",
                "is_bye": True,
            })
            continue

        if not rating_text.isdigit() or len(rating_text) < 3:
            continue

        opponent_rating = int(rating_text)

        result_clean = result_text.strip().replace(' ', '')
        is_forfeit = '0K' in result_clean or '1K' in result_clean

        if result_clean in ('1', '1.0', '+') or '1K' in result_clean:
            result_val = 1.0
        elif result_clean in ('0', '0.0', '-') or '0K' in result_clean:
            result_val = 0.0
        elif result_clean in (half_char, '1/2', '0.5'):
            result_val = 0.5
        else:
            continue

        game_entry = {
            "opponent_rating": opponent_rating,
            "result": result_val,
            "opponent_name": name_text,
        }
        if is_forfeit:
            game_entry["is_forfeit"] = True
        games.append(game_entry)

    return player_rating, games


def calculate_new_rating(old_rating, games, k=40, limit_400=True):
    total_expected_score = 0
    actual_rating_score = 0
    actual_display_score = 0
    game_expected_scores = []

    for game in games:
        actual_display_score += game['result']

        if game.get('is_bye') or game.get('is_forfeit'):
            game_expected_scores.append(None)
            continue

        actual_rating_score += game['result']

        opponent_rating = game['opponent_rating']
        diff = opponent_rating - old_rating
        if limit_400:
            diff = max(min(diff, 400), -400)

        expected_score = 1 / (1 + 10 ** (diff / 400))
        game_expected_scores.append(round(expected_score, 2))
        total_expected_score += expected_score

    rating_change = k * (actual_rating_score - total_expected_score)
    new_rating = old_rating + round(rating_change)
    return new_rating, actual_display_score, round(total_expected_score, 2), game_expected_scores
