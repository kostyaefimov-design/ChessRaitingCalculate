import requests
from bs4 import BeautifulSoup
import re


def parse_player_page(url):
    """
    Parse a chess-results.com player page and extract:
    - the player's current rating
    - the list of played games (opponent, result, opponent rating)

    Returns (player_rating, games):
        player_rating (int | None) — current rating of the player
        games (list[dict]) — list of game dicts, each with:
            opponent_rating (int | None)
            result (float): 1.0 = win, 0.5 = draw, 0.0 = loss
            opponent_name (str)
            is_bye (bool, optional): True if this was a bye round
            is_forfeit (bool, optional): True if this was a forfeit (kampflos)
    """
    # --- Step 1: Fetch the HTML page ---
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=(5, 10))
        response.raise_for_status()
    except requests.RequestException:
        return None, None

    # --- Step 2: Find the player's current rating ---
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

    # --- Step 3: Find the game results table ---
    game_table = None
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        has_rnd = any(h in headers for h in ('Тур', 'Rd.'))
        has_rtg = any(h in headers for h in ('Рейт.', 'Rtg'))
        has_res = any(h in headers for h in ('Рез.', 'Res.'))
        if has_rnd and has_rtg and has_res:
            game_table = table
            break

    if game_table is None:
        return player_rating, games

    # --- Step 4: Determine column indices (supports RU and EN) ---
    header_cells = game_table.find_all('th')
    col_index = {}
    for i, th in enumerate(header_cells):
        text = th.get_text(strip=True)
        if text in ('Рейт.', 'Rtg'):
            col_index['rating'] = i
        elif text in ('Рез.', 'Res.'):
            col_index['result'] = i
        elif text in ('Имя', 'Name'):
            col_index['name'] = i

    if 'rating' not in col_index or 'result' not in col_index:
        return player_rating, games

    # --- Step 5: Parse each game row ---
    half_char = '\u00bd'

    for row in game_table.find_all('tr'):
        cells = row.find_all('td')
        min_required = max(col_index.values())
        if len(cells) <= min_required:
            continue

        rating_text = cells[col_index['rating']].get_text(strip=True)
        result_text = cells[col_index['result']].get_text(strip=True)
        name_text = cells[col_index.get('name', 0)].get_text(strip=True) if 'name' in col_index else ""

        # --- Check for BYE round ---
        # BYE: no opponent rating, name contains a bye keyword
        # 'freilos' = German bye, 'входной' = Russian bye
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

        # --- Parse result value ---
        # Strip spaces so "- 0K" becomes "-0K"
        result_clean = result_text.strip().replace(' ', '')
        # "K" stands for German "kampflos" (without fight) — forfeit result
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
    """
    Calculate the new Elo rating after a list of games.

    Parameters:
        old_rating (int) — player's rating before the tournament
        games (list[dict]) — list of game dicts from parse_player_page()
        k (int) — Elo K-factor (40, 20, or 10)
        limit_400 (bool) — cap rating difference at ±400 (FIDE rule)

    Returns (new_rating, actual_display_score, total_expected_score, game_expected_scores):
        new_rating (int) — rating rounded to integer
        actual_display_score (float) — sum of points from ALL games (including bye/forfeit)
        total_expected_score (float) — sum of expected scores (bye/forfeit excluded)
        game_expected_scores (list[float|None]) — expected score per game, None for bye/forfeit

    Elo formula:
        E = 1 / (1 + 10^((R_opponent - R_player) / 400))
        ΔR = K * (S - ΣE)
        new_rating = old_rating + round(ΔR)

    The ±400 cap prevents absurd expected scores when rating gaps are extreme,
    e.g. 1000 vs 2800 without cap would give expected ≈ 0.0000003,
    making a win worth ~40 points instead of a reasonable ~39.
    """
    total_expected_score = 0.0
    actual_rating_score = 0.0
    actual_display_score = 0.0
    game_expected_scores = []

    for game in games:
        actual_display_score += game['result']

        # Bye and forfeit games are not actual played games — skip Elo calculation
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
