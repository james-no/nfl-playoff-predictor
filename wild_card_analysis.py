"""
Analyze how EPA predictions performed for 2025 Wild Card Weekend
"""

import nflreadpy as nfl
import polars as pl

def fetch_nfl_data(season=2025):
    """Fetch NFL play-by-play data with EPA metrics"""
    print(f"📥 Fetching {season} NFL data...\n")
    
    try:
        pbp = nfl.load_pbp([season])
        pbp = pbp.filter((pl.col('rush') == 1) | (pl.col('pass') == 1))
        pbp = pbp.filter(pl.col('season_type') == 'REG')
        pbp = pbp.to_pandas()
        
        print(f"✅ Loaded {len(pbp)} plays from {season} season\n")
        return pbp
        
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        return None

def calculate_team_epa(pbp):
    """Calculate offensive and defensive EPA for all teams"""
    offense = pbp.groupby('posteam')['epa'].agg(['mean', 'count']).reset_index()
    offense.columns = ['team', 'off_epa', 'off_plays']
    
    defense = pbp.groupby('defteam')['epa'].agg(['mean', 'count']).reset_index()
    defense.columns = ['team', 'def_epa', 'def_plays']
    
    team_stats = offense.merge(defense, on='team')
    
    return team_stats

def get_team_stats(team_stats, team_abbr):
    """Get stats for a specific team"""
    team_data = team_stats[team_stats['team'] == team_abbr]
    
    if team_data.empty:
        return None
    
    return {
        'team': team_abbr,
        'off_epa': float(team_data['off_epa'].values[0]),
        'def_epa': float(team_data['def_epa'].values[0]),
    }

def predict_winner(team1_stats, team2_stats):
    """Predict winner based on EPA differential"""
    # Calculate EPA advantage (positive = team1 advantage)
    off_diff = team1_stats['off_epa'] - team2_stats['off_epa']
    def_diff = team2_stats['def_epa'] - team1_stats['def_epa']  # Lower def EPA is better
    
    total_advantage = off_diff + def_diff
    
    # Simple win probability based on EPA differential
    win_prob = 50 + (total_advantage * 100)
    win_prob = max(20, min(80, win_prob))
    
    return 'team1' if total_advantage > 0 else 'team2', win_prob if total_advantage > 0 else (100 - win_prob)

def main():
    """Main function"""
    
    print("\n" + "🏈" * 35)
    print("2025 WILD CARD WEEKEND - EPA PREDICTION ANALYSIS".center(70))
    print("🏈" * 35 + "\n")
    
    pbp = fetch_nfl_data(2025)
    
    if pbp is None:
        print("Failed to load data. Exiting.")
        return
    
    team_stats = calculate_team_epa(pbp)
    
    # Wild Card games with actual results
    games = [
        ("LA", "CAR", "LA", 34, 31),  # Rams won 34-31
        ("CHI", "GB", "CHI", 31, 27),  # Bears won 31-27
        ("BUF", "JAX", "BUF", 27, 24),  # Bills won 27-24
        ("SF", "PHI", "SF", 23, 19),  # 49ers won 23-19
        ("NE", "LAC", "NE", 16, 3),  # Patriots won 16-3
        ("HOU", "PIT", "HOU", 30, 6),  # Texans won 30-6
    ]
    
    correct = 0
    total = len(games)
    
    print("=" * 90)
    print("GAME-BY-GAME ANALYSIS".center(90))
    print("=" * 90 + "\n")
    
    for team1, team2, actual_winner, score1, score2 in games:
        t1_stats = get_team_stats(team_stats, team1)
        t2_stats = get_team_stats(team_stats, team2)
        
        predicted, prob = predict_winner(t1_stats, t2_stats)
        predicted_team = team1 if predicted == 'team1' else team2
        
        was_correct = (predicted_team == actual_winner)
        correct += was_correct
        
        print(f"{'✅' if was_correct else '❌'} {team1} vs {team2}")
        print(f"   Actual Result: {actual_winner} wins {score1}-{score2}")
        print(f"   EPA Prediction: {predicted_team} ({prob:.0f}%)")
        print(f"   {team1} EPA: Off {t1_stats['off_epa']:+.4f} | Def {t1_stats['def_epa']:+.4f}")
        print(f"   {team2} EPA: Off {t2_stats['off_epa']:+.4f} | Def {t2_stats['def_epa']:+.4f}")
        
        if not was_correct:
            losing_prob = 100 - prob
            print(f"   ⚠️  UPSET! Underdog had {losing_prob:.0f}% chance")
        
        print()
    
    print("=" * 90)
    print(f"FINAL ACCURACY: {correct}/{total} ({correct/total*100:.1f}%)")
    print("=" * 90)
    
    if correct < total:
        print(f"\n📊 Missed Predictions: {total - correct}")
        print("The upsets were games where the EPA underdog won.")

if __name__ == "__main__":
    main()
