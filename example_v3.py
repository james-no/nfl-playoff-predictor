"""
Example usage of NFL Predictor v3.0

This demonstrates how to use the refactored OOP architecture.
"""

from core.predictor import NFLPredictor

def main():
    """Run example predictions for NFL playoffs."""
    
    print("🏈 NFL Playoff Predictor v3.0")
    print("=" * 80)
    
    # Initialize predictor
    predictor = NFLPredictor()
    
    # Example 1: Divisional Round prediction with all context
    print("\n📍 DIVISIONAL ROUND EXAMPLE\n")
    
    prediction = predictor.predict_game(
        home_team='DEN',
        away_team='BUF',
        injuries={
            'DEN': 0.0,  # No major injuries
            'BUF': -0.02  # Minor injuries
        },
        weather={
            'temperature': 35,  # Cold game
            'wind_speed': 12,   # Moderate wind
            'precipitation': 0  # No precipitation
        },
        rest_days={
            'home': 13,  # Bye week
            'away': 6    # Played wild card
        },
        odds=-110,
        bankroll=10000
    )
    
    # Format and print prediction
    output = predictor.format_prediction_output(prediction)
    print(output)
    
    # Example 2: Simple prediction without extra context
    print("\n📍 SIMPLE PREDICTION EXAMPLE\n")
    
    simple_prediction = predictor.predict_game(
        home_team='SF',
        away_team='GB'
    )
    
    print(predictor.format_prediction_output(simple_prediction))
    
    # Show database stats if available
    if predictor.db:
        stats = predictor.db.get_performance_stats(days=30)
        print("\n📊 Performance Stats (Last 30 Days):")
        print(f"  Total Predictions: {stats['total_predictions']}")
        print(f"  Accuracy (SU): {stats['accuracy_su']:.1%}")
        print(f"  Accuracy (ATS): {stats['accuracy_ats']:.1%}")
        print(f"  Average CLV: {stats['avg_clv']:+.2f}")
        print(f"  Total Profit: ${stats['total_profit']:.2f}")
        print(f"  ROI: {stats['roi']:+.1f}%\n")


if __name__ == "__main__":
    main()
