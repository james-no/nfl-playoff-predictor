"""Input validation utilities."""

from config import TeamsConfig


def validate_team(team: str) -> bool:
    """
    Validate team abbreviation.
    
    Args:
        team: Team abbreviation (e.g., 'DEN')
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If invalid team
    """
    valid_teams = TeamsConfig.ALL_TEAMS
    
    if team not in valid_teams:
        raise ValueError(
            f"Invalid team '{team}'. Must be one of: {', '.join(sorted(valid_teams))}"
        )
    
    return True


def validate_probability(prob: float) -> bool:
    """
    Validate probability value.
    
    Args:
        prob: Probability (0-1)
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If invalid probability
    """
    if not 0 <= prob <= 1:
        raise ValueError(f"Probability must be between 0 and 1, got {prob}")
    
    return True


def validate_odds(odds: int) -> bool:
    """
    Validate American odds.
    
    Args:
        odds: American odds
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If invalid odds
    """
    if odds == 0 or (odds > -100 and odds < 100 and odds != 0):
        raise ValueError(f"Invalid American odds: {odds}")
    
    return True


def are_division_rivals(team1: str, team2: str) -> bool:
    """
    Check if two teams are division rivals.
    
    Args:
        team1: First team abbreviation
        team2: Second team abbreviation
        
    Returns:
        True if division rivals
    """
    validate_team(team1)
    validate_team(team2)
    
    divisions = TeamsConfig.DIVISIONS
    
    for division_teams in divisions.values():
        if team1 in division_teams and team2 in division_teams:
            return True
    
    return False
