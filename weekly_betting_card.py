"""
Weekly Betting Card Generator
Run this script each week to get betting recommendations based on current market lines.
"""
from core.betting_signals import BettingSignalGenerator
from core.predictor import NFLPredictor
from core.data_loader import NFLDataLoader
from config import BettingConfig
from utils.playoff_validator import (
    validate_playoff_matchup, 
    get_divisional_matchups_2026,
    print_current_bracket,
    get_elimination_message
)

# =============================================================================
# DIVISIONAL ROUND - JANUARY 2026
# =============================================================================

def get_weather_forecasts():
    """
    Weather forecasts for Divisional Round games.
    
    Update these from:
    - Weather.gov
    - Weather Underground
    - Dark Sky API
    
    Check 24-48 hours before kickoff for accuracy.
    """
    return {
        "BUF @ DEN": {'temperature': 28, 'wind_speed': 12, 'precipitation': 0},  # Mile High - cold
        "SF @ SEA": {'temperature': 45, 'wind_speed': 8, 'precipitation': 1},   # Seattle - typical
        "HOU @ NE": {'temperature': 32, 'wind_speed': 10, 'precipitation': 0},  # Foxboro - cold
        "LA @ CHI": {'temperature': 35, 'wind_speed': 15, 'precipitation': 0},  # Chicago - windy
    }

def get_divisional_round_lines():
    """
    Current market lines for Divisional Round (as of 1/15/2026).
    
    Format: "AWAY @ HOME": spread (positive = home favored)
    
    Update these from:
    - VegasInsider.com
    - Pro-Football-Reference.com  
    - The Action Network
    - Covers.com
    """
    return {
        "BUF @ DEN": 5.5,     # Broncos -5.5
        "HOU @ NE": 3.5,      # Patriots -3.5
        "SF @ SEA": 7.5,      # Seahawks -7.5
        "LA @ CHI": 3.0,      # Bears -3
    }


# Set your bankroll (used by signal generator)
BANKROLL = 10000  # $10,000

def generate_weekly_card():
    """Generate betting recommendations for upcoming games."""
    
    # Show current playoff status
    print_current_bracket()
    
    # Use official matchups from validator
    games = get_divisional_matchups_2026()
    
    # Validate all matchups before proceeding
    print("Validating playoff matchups...")
    for game in games:
        is_valid, error_msg = validate_playoff_matchup(game['home'], game['away'])
        if not is_valid:
            print(f"\n❌ {error_msg}")
            print(f"   {get_elimination_message(game['home'])}")
            print(f"   {get_elimination_message(game['away'])}")
            print("\n⚠️  Please update weekly_betting_card.py with correct teams!\n")
            return None
        print(f"  ✓ {game['away']} @ {game['home']} - Valid")
    
    print("\n✅ All matchups validated!\n")
    
    print("Loading 2025 season data...")
    data_loader = NFLDataLoader(season=2025)
    pbp_data = data_loader.load_play_by_play()
    
    print("Initializing predictor...")
    predictor = NFLPredictor()
    
    print("Running predictions...\n")
    predictions = []
    
    # Load weather forecasts
    weather_forecasts = get_weather_forecasts()
    
    for game in games:
        game_key = f"{game['away']} @ {game['home']}"
        print(f"Analyzing {game_key}...")
        
        # Get weather for this specific game
        weather = weather_forecasts.get(game_key)
        if weather is None:
            print(f"  ⚠️  No weather forecast found for {game_key}, using defaults")
            weather = {'temperature': 50, 'wind_speed': 5, 'precipitation': 0}
        else:
            print(f"  🌤  Weather: {weather['temperature']}°F, Wind: {weather['wind_speed']}mph")
        
        pred = predictor.predict_game(
            home_team=game['home'],
            away_team=game['away'],
            weather=weather,
            rest_days={'home': 7, 'away': 7},  # Standard week rest
            is_playoff=True,  # Divisional Round
            save_to_db=False  # Don't clutter DB during testing
        )
        
        # Add game date to prediction for CSV export
        pred['game_date'] = game.get('date', 'TBD')
        
        predictions.append(pred)
    
    # Get current market lines
    market_lines = get_divisional_round_lines()
    
    # Generate betting signals
    print("\n" + "="*80)
    print("GENERATING BETTING RECOMMENDATIONS")
    print("="*80 + "\n")
    
    signal_generator = BettingSignalGenerator(bankroll=BANKROLL)
    recommendations = signal_generator.generate_weekly_card(
        predictions=predictions,
        market_lines=market_lines,
        is_playoff=True
    )
    
    # Print full betting card
    signal_generator.print_weekly_card(recommendations)
    
    # Export to CSV for record keeping
    export_to_csv(recommendations)
    
    return recommendations


def export_to_csv(recommendations):
    """Export recommendations to CSV for tracking."""
    import pandas as pd
    from datetime import datetime
    
    data = []
    for rec in recommendations:
        # Extract game date from the recommendation if available
        game_date = getattr(rec, 'game_date', 'TBD')
        
        data.append({
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'game_date': game_date,
            'game': rec.game,
            'signal': rec.signal.value,
            'recommended_side': rec.recommended_side,
            'model_spread': rec.model_spread,
            'market_spread': rec.market_spread,
            'edge_points': rec.edge_points,
            'suggested_units': rec.suggested_units,
            'confidence': rec.confidence
        })
    
    df = pd.DataFrame(data)
    filename = f"betting_card_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(filename, index=False)
    print(f"\n✅ Betting card exported to {filename}")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           NFL PLAYOFF BETTING CARD GENERATOR v3.0            ║
    ║                                                              ║
    ║  This script generates weekly betting recommendations        ║
    ║  by comparing your model's predictions to market lines.      ║
    ║                                                              ║
    ║  INSTRUCTIONS:                                               ║
    ║  1. Update utils/playoff_validator.py with current teams     ║
    ║  2. Update market lines in get_divisional_round_lines()      ║
    ║  3. Update weather forecasts for each game                   ║
    ║  4. Run this script: python weekly_betting_card.py           ║
    ║  5. Review STRONG BET recommendations                        ║
    ║  6. Place bets according to suggested unit sizing            ║
    ║                                                              ║
    ║  ⚠️  ALWAYS verify lines before betting!                     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    recommendations = generate_weekly_card()
    
    if recommendations is None:
        print("❌ Betting card generation failed due to invalid matchups.")
        print("   Please update utils/playoff_validator.py with correct teams.\n")
        exit(1)
    
    # Show only strong bets for quick reference
    print("\n" + "="*80)
    print("🔥 QUICK REFERENCE: STRONG BETS ONLY")
    print("="*80)
    
    strong_bets = [r for r in recommendations if r.signal.value == "STRONG BET"]
    
    if strong_bets:
        for rec in strong_bets:
            print(f"\n{rec.game}")
            print(f"  → BET: {rec.recommended_side}")
            print(f"  → UNITS: {rec.suggested_units:.1f} (${rec.suggested_units * 100:.0f})")
            print(f"  → EDGE: {rec.edge_points:.1f} points")
    else:
        print("\nNo strong bet recommendations this week.")
        print("Consider waiting for better spots or reviewing MEDIUM BET options.")
    
    print("\n" + "="*80)
    print("Good luck! 🍀")
    print("="*80 + "\n")
