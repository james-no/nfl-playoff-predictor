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
    
    for game in games:
        print(f"Analyzing {game['away']} @ {game['home']}...")
        
        pred = predictor.predict_game(
            home_team=game['home'],
            away_team=game['away'],
            weather={
                'temperature': 35,  # Update with actual forecast
                'wind_speed': 10,
                'precipitation': 0
            },
            rest_days={'home': 7, 'away': 7},  # Standard week rest
            is_playoff=True,  # Divisional Round
            save_to_db=False  # Don't clutter DB during testing
        )
        
        predictions.append(pred)
    
    # Get current market lines
    market_lines = get_divisional_round_lines()
    
    # Generate betting signals
    print("\n" + "="*80)
    print("GENERATING BETTING RECOMMENDATIONS")
    print("="*80 + "\n")
    
    signal_generator = BettingSignalGenerator(bankroll=10000)
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
        data.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
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
    # Set your bankroll
    BANKROLL = 10000  # $10,000
    
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
