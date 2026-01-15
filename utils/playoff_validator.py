"""
Playoff Team Validator
Ensures we only analyze teams that are actually still in the playoffs.
"""
from typing import List, Dict
from datetime import datetime


# Update this each week with remaining playoff teams
PLAYOFF_TEAMS_2026 = {
    'wild_card': {
        'afc': ['BUF', 'JAX', 'NE', 'LAC', 'HOU', 'PIT'],
        'nfc': ['SF', 'PHI', 'LA', 'CAR', 'CHI', 'GB']
    },
    'divisional': {
        'afc': ['BUF', 'DEN', 'NE', 'HOU'],
        'nfc': ['SF', 'SEA', 'LA', 'CHI']
    },
    'conference': {
        'afc': [],  # TBD after divisional
        'nfc': []   # TBD after divisional
    },
    'super_bowl': {
        'afc': [],  # TBD after conference
        'nfc': []   # TBD after conference
    }
}

# Current round (update this each week)
CURRENT_ROUND = 'divisional'


def get_active_playoff_teams() -> List[str]:
    """
    Get list of teams still active in current playoff round.
    
    Returns:
        List of team abbreviations still in playoffs
    """
    round_teams = PLAYOFF_TEAMS_2026.get(CURRENT_ROUND, {})
    afc = round_teams.get('afc', [])
    nfc = round_teams.get('nfc', [])
    return afc + nfc


def validate_playoff_team(team: str) -> bool:
    """
    Check if a team is still in the playoffs.
    
    Args:
        team: Team abbreviation
        
    Returns:
        True if team is still active in playoffs
    """
    active_teams = get_active_playoff_teams()
    return team in active_teams


def validate_playoff_matchup(home_team: str, away_team: str) -> tuple[bool, str]:
    """
    Validate that both teams in a matchup are in the playoffs.
    
    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    active_teams = get_active_playoff_teams()
    
    if home_team not in active_teams and away_team not in active_teams:
        return False, f"ERROR: Neither {home_team} nor {away_team} are in the {CURRENT_ROUND} round!"
    
    if home_team not in active_teams:
        return False, f"ERROR: {home_team} has been ELIMINATED from playoffs!"
    
    if away_team not in active_teams:
        return False, f"ERROR: {away_team} has been ELIMINATED from playoffs!"
    
    return True, ""


def get_divisional_matchups_2026() -> List[Dict]:
    """
    Get the official Divisional Round matchups for 2026.
    
    Returns:
        List of matchup dicts with home/away teams
    """
    return [
        {"home": "DEN", "away": "BUF", "time": "Saturday 4:30 PM ET"},
        {"home": "SEA", "away": "SF", "time": "Saturday 8:00 PM ET"},
        {"home": "NE", "away": "HOU", "time": "Sunday 3:00 PM ET"},
        {"home": "CHI", "away": "LA", "time": "Sunday 6:30 PM ET"},
    ]


def print_current_bracket():
    """Print the current playoff bracket status."""
    print("\n" + "="*80)
    print(f"CURRENT PLAYOFF STATUS: {CURRENT_ROUND.upper()} ROUND")
    print("="*80)
    
    active = get_active_playoff_teams()
    
    round_teams = PLAYOFF_TEAMS_2026[CURRENT_ROUND]
    
    print("\nAFC:")
    for team in round_teams['afc']:
        print(f"  ✓ {team}")
    
    print("\nNFC:")
    for team in round_teams['nfc']:
        print(f"  ✓ {team}")
    
    print("\n" + "="*80)
    
    if CURRENT_ROUND == 'divisional':
        print("\nDIVISIONAL ROUND MATCHUPS:")
        for matchup in get_divisional_matchups_2026():
            print(f"  • {matchup['away']} @ {matchup['home']} ({matchup['time']})")
    
    print("="*80 + "\n")


# Eliminated teams (for error messages)
ELIMINATED_TEAMS_2026 = [
    'KC', 'BAL', 'PHI', 'DET', 'GB', 'CAR', 'JAX', 'PIT', 'LAC',  # After Wild Card
    # Add more as rounds progress
]


def get_elimination_message(team: str) -> str:
    """Get helpful message about when a team was eliminated."""
    if team in ['JAX', 'PIT', 'LAC', 'PHI', 'GB', 'CAR']:
        return f"{team} was eliminated in Wild Card Weekend"
    elif team in ['KC', 'BAL', 'DET']:
        return f"{team} missed the playoffs entirely"
    else:
        return f"{team} is not in the current playoff bracket"


# Instructions for updating each week
WEEKLY_UPDATE_INSTRUCTIONS = """
===============================================================================
🔴 IMPORTANT: UPDATE THIS FILE EACH WEEK 🔴
===============================================================================

After each playoff round, update the following:

1. Set CURRENT_ROUND to:
   - 'wild_card' (Week 1 of playoffs)
   - 'divisional' (Week 2 of playoffs)
   - 'conference' (Week 3 of playoffs)
   - 'super_bowl' (Week 4 of playoffs)

2. Update PLAYOFF_TEAMS_2026[CURRENT_ROUND] with teams still alive:
   - Remove losers from previous round
   - Add only teams that WON and advanced

3. Add eliminated teams to ELIMINATED_TEAMS_2026

4. If divisional/conference/super_bowl, update the matchup function with
   actual games from official NFL schedule

===============================================================================
"""
