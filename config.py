"""
Configuration Management for NFL Playoff Predictor
All constants, settings, and configurable parameters in one place
"""

import os
from datetime import datetime

# =============================================================================
# SEASON & DATA SETTINGS
# =============================================================================

class SeasonConfig:
    """Season and data-related configuration"""
    
    # Auto-detect current season based on date
    @staticmethod
    def get_current_season():
        """
        Auto-detect NFL season based on current date
        
        Returns:
            tuple: (season_year, phase)
            
        Examples:
            January 2026 -> (2025, "Playoffs")
            September 2026 -> (2026, "Regular Season")
        """
        now = datetime.now()
        year = now.year
        month = now.month
        
        if month <= 2:  # Jan-Feb: Playoffs
            return year - 1, "Playoffs"
        elif month <= 8:  # Mar-Aug: Offseason
            return year - 1, "Offseason"
        else:  # Sept-Dec: Regular Season
            return year, "Regular Season"
    
    # Data fetch settings
    CACHE_ENABLED = True
    CACHE_HOURS = 24
    CACHE_DURATION_HOURS = 24
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5

# =============================================================================
# EPA & STATISTICAL SETTINGS
# =============================================================================

class EPAConfig:
    """EPA calculation and weighting configuration"""
    
    # Weighting for recent vs full season
    RECENT_GAMES = 4
    RECENT_GAMES_WINDOW = 4  # Last 4 games
    RECENT_FORM_WEIGHT = 0.70  # 70% weight on recent form
    FULL_SEASON_WEIGHT = 0.30  # 30% weight on full season

    # EPA-dominant mode and caps
    EPA_DOMINANT_MODE = True
    GLOBAL_NON_EPA_CAP = 0.060  # Max absolute differential added by non-EPA factors (~1.5 pts)
    CAP_REST_EPA = 0.035
    CAP_INJURY_PER_TEAM_EPA = 0.030  # Generic per-team injury cap (QB-specific TBD)
    CAP_FAN_NOISE_EPA = 0.009
    CAP_WEATHER_EPA = 0.030
    
    # EPA thresholds
    ELITE_OFFENSE_THRESHOLD = 0.15
    ELITE_DEFENSE_THRESHOLD = -0.08
    
    # Situational stats
    THIRD_DOWN_MIN_DISTANCE = 4  # 3rd & 4-7 is most critical
    THIRD_DOWN_MAX_DISTANCE = 7
    RED_ZONE_YARDLINE = 20  # Inside 20 yard line
    
    # Explosive plays
    EXPLOSIVE_PLAY_YARDS = 20  # 20+ yards

# =============================================================================
# BETTING & PREDICTION SETTINGS
# =============================================================================

class BettingConfig:
    """Betting analysis configuration"""
    
    # Home field advantage
    HOME_FIELD_EPA = 0.029  # ~2.5 points
    
    # Environmental factors
    ALTITUDE_ADVANTAGE_EPA = 0.018  # Denver Mile High
    COLD_WEATHER_PENALTY = -0.010  # Per 10 degrees below 40F
    WIND_PENALTY_PER_MPH = -0.001  # Per MPH over 15
    
    # Crowd noise (home defense disrupts away offense, esp. snap counts)
    FAN_NOISE_BASE_EPA = 0.004  # Applied for all home teams in playoffs
    FAN_NOISE_LOUD_STADIUM_BONUS_EPA = 0.003  # Extra for known loud venues
    FAN_NOISE_DOME_BONUS_EPA = 0.002  # Extra if dome team at home
    
    # Division rivalry
    DIVISION_RIVALRY_COMPRESSION = 0.18  # Games 18% closer than expected
    RIVALRY_EPA_COMPRESSION = 0.18  # Alias
    
    # Rest differential
    BYE_WEEK_ADVANTAGE_EPA = 0.035  # ~3 points
    
    # Kelly Criterion
    FULL_KELLY = 1.0
    HALF_KELLY = 0.5
    QUARTER_KELLY = 0.25  # Recommended (safest)
    KELLY_FRACTION = 0.25
    RECOMMENDED_KELLY = QUARTER_KELLY
    
    # Bet sizing
    DEFAULT_BANKROLL = 10000  # $10,000
    MIN_BET_SIZE = 50  # $50 minimum
    MAX_BET_SIZE_PCT = 0.05  # 5% of bankroll max
    
    # American odds
    DEFAULT_ODDS = -110  # Standard juice
    
    # Key numbers (most common margins)
    KEY_NUMBERS = [3, 7, 10, 6, 4, 14]

# =============================================================================
# TRAVEL SETTINGS
# =============================================================================

class TravelConfig:
    """Travel and timezone impact configuration"""
    
    # Penalty applied to away team EPA based on timezone difference
    TZ_DIFF_PENALTY = {
        0: 0.0,
        1: -0.007,
        2: -0.012,
        3: -0.018,
    }
    
    # Additional penalty multiplier if away team is on a short week (< 7 rest days)
    SHORT_WEEK_MULTIPLIER = 1.5

    # Hard cap for total travel penalty (e.g., 3 zones with short week → -0.027)
    MAX_PENALTY_EPA = -0.027
    
    # Early East kickoffs for West teams (optional future)
    EARLY_EAST_KICK_PENALTY = -0.004  # Not applied by default

# =============================================================================
# INJURY IMPACT SETTINGS
# =============================================================================

class InjuryConfig:
    """Injury impact weights by position"""
    
    # Impact scale (EPA)
    STARTER_QB_OUT = 0.040
    BACKUP_QB_PLAYING = 0.015
    LEFT_TACKLE = 0.030
    RIGHT_TACKLE = 0.025
    CENTER = 0.020
    GUARD = 0.015
    ELITE_EDGE_RUSHER = 0.025
    ELITE_DT = 0.015
    WR1 = 0.020
    WR2 = 0.012
    ELITE_TE = 0.025
    RB = 0.010  # Most replaceable
    CB1 = 0.018
    SAFETY = 0.012
    
    # Status multipliers
    OUT_MULTIPLIER = 1.0
    DOUBTFUL_MULTIPLIER = 0.8
    QUESTIONABLE_MULTIPLIER = 0.5
    PROBABLE_MULTIPLIER = 0.2
    PLAYING_HURT_MULTIPLIER = 0.3

# =============================================================================
# REFEREE CREW SETTINGS
# =============================================================================

class RefereeConfig:
    """Referee crew tendencies"""
    
    # Average NFL crew
    AVG_PENALTIES_PER_GAME = 11.5
    AVG_PENALTY_YARDS = 92
    
    # Over/Under impact
    FLAG_HEAVY_CREW_OVER_IMPACT = 3.0  # Add 3 points to total
    FLAG_LIGHT_CREW_UNDER_IMPACT = -2.0  # Subtract 2 points

# =============================================================================
# DATABASE SETTINGS
# =============================================================================

class DatabaseConfig:
    """Database configuration"""
    
    DB_PATH = "nfl_predictions.db"
    ENABLE_TRACKING = True
    AUTO_BACKUP = True
    BACKUP_INTERVAL_DAYS = 7

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

class LoggingConfig:
    """Logging configuration"""
    
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE = "nfl_predictor.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_TO_CONSOLE = True
    LOG_TO_FILE = True
    MAX_LOG_SIZE_MB = 10
    BACKUP_COUNT = 3

# =============================================================================
# API & EXTERNAL SERVICE SETTINGS
# =============================================================================

class APIConfig:
    """External API configuration"""
    
    # Azure OpenAI (optional - for AI analysis)
    AZURE_ENDPOINT = "https://foundry0012.cognitiveservices.azure.com/"
    AZURE_DEPLOYMENT = "gpt-4.1"
    AZURE_API_VERSION = "2024-12-01-preview"
    AZURE_API_KEY = os.getenv("AZURE_API_KEY", "")
    
    # NFL Data
    NFL_DATA_TIMEOUT_SECONDS = 30
    
    # Weather API (placeholder for future)
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
    WEATHER_API_ENABLED = False

# =============================================================================
# UI SETTINGS
# =============================================================================

class UIConfig:
    """UI/UX configuration"""
    
    APP_TITLE = "NFL Playoff Predictor v3.0"
    APP_ICON = "🏈"
    PAGE_LAYOUT = "wide"
    THEME_COLOR = "green"
    
    # Display settings
    SHOW_DETAILED_STATS = True
    SHOW_CONFIDENCE_INTERVALS = True
    SHOW_INJURY_REPORTS = True
    SHOW_BETTING_INTEL = True

# =============================================================================
# VALIDATION SETTINGS
# =============================================================================

class ValidationConfig:
    """Validation and testing configuration"""
    
    # Backtesting
    MIN_SAMPLE_SIZE = 20  # Min games for statistical significance
    PROFITABILITY_THRESHOLD = 0.53  # 53% ATS needed to beat juice
    
    # Model validation
    MAX_PREDICTION_AGE_HOURS = 24  # Predictions expire after 24 hours
    CONFIDENCE_THRESHOLD_HIGH = 0.65  # 65%+ = high confidence
    CONFIDENCE_THRESHOLD_LOW = 0.55  # <55% = low confidence

# =============================================================================
# TEAM ABBREVIATIONS
# =============================================================================

class TeamsConfig:
    """NFL team information"""
    
    AFC_EAST = ['BUF', 'MIA', 'NE', 'NYJ']
    AFC_NORTH = ['BAL', 'CIN', 'CLE', 'PIT']
    AFC_SOUTH = ['HOU', 'IND', 'JAX', 'TEN']
    AFC_WEST = ['DEN', 'KC', 'LV', 'LAC']
    
    NFC_EAST = ['DAL', 'NYG', 'PHI', 'WAS']
    NFC_NORTH = ['CHI', 'DET', 'GB', 'MIN']
    NFC_SOUTH = ['ATL', 'CAR', 'NO', 'TB']
    NFC_WEST = ['ARI', 'LA', 'SF', 'SEA']
    
    ALL_TEAMS = (AFC_EAST + AFC_NORTH + AFC_SOUTH + AFC_WEST +
                 NFC_EAST + NFC_NORTH + NFC_SOUTH + NFC_WEST)
    
    # Division dictionary for rivalry checking
    DIVISIONS = {
        'AFC_EAST': AFC_EAST,
        'AFC_NORTH': AFC_NORTH,
        'AFC_SOUTH': AFC_SOUTH,
        'AFC_WEST': AFC_WEST,
        'NFC_EAST': NFC_EAST,
        'NFC_NORTH': NFC_NORTH,
        'NFC_SOUTH': NFC_SOUTH,
        'NFC_WEST': NFC_WEST,
    }

    # Team timezones for travel impact
    TEAM_TIMEZONES = {
        # AFC East (ET)
        'BUF': 'ET', 'MIA': 'ET', 'NE': 'ET', 'NYJ': 'ET',
        # AFC North (ET)
        'BAL': 'ET', 'CIN': 'ET', 'CLE': 'ET', 'PIT': 'ET',
        # AFC South
        'HOU': 'CT', 'IND': 'ET', 'JAX': 'ET', 'TEN': 'CT',
        # AFC West
        'DEN': 'MT', 'KC': 'CT', 'LV': 'PT', 'LAC': 'PT',
        # NFC East
        'DAL': 'CT', 'NYG': 'ET', 'PHI': 'ET', 'WAS': 'ET',
        # NFC North
        'CHI': 'CT', 'DET': 'ET', 'GB': 'CT', 'MIN': 'CT',
        # NFC South
        'ATL': 'ET', 'CAR': 'ET', 'NO': 'CT', 'TB': 'ET',
        # NFC West
        'ARI': 'MT', 'LA': 'PT', 'SF': 'PT', 'SEA': 'PT',
    }
    
    # Teams with special factors
    ALTITUDE_TEAMS = ['DEN']  # Mile High
    COLD_WEATHER_TEAMS = ['BUF', 'GB', 'CHI', 'DEN', 'NE']
    DOME_TEAMS = ['ATL', 'DET', 'NO', 'MIN', 'LV', 'LA', 'ARI']
    
    # Known loud stadiums (historically top crowd noise)
    LOUD_STADIUMS = ['SEA', 'KC', 'NO', 'BUF', 'PHI', 'GB', 'DAL', 'MIN']

# =============================================================================
# EXPORT ALL CONFIGS
# =============================================================================

# Easy access to all configs
CONFIG = {
    'season': SeasonConfig,
    'epa': EPAConfig,
    'betting': BettingConfig,
    'injury': InjuryConfig,
    'referee': RefereeConfig,
    'database': DatabaseConfig,
    'logging': LoggingConfig,
    'api': APIConfig,
    'ui': UIConfig,
    'validation': ValidationConfig,
    'teams': TeamsConfig,
}

def get_config(category: str):
    """
    Get configuration for a specific category
    
    Args:
        category: One of 'season', 'epa', 'betting', etc.
        
    Returns:
        Configuration class for that category
        
    Example:
        >>> betting_cfg = get_config('betting')
        >>> print(betting_cfg.HOME_FIELD_EPA)
        0.029
    """
    return CONFIG.get(category)
