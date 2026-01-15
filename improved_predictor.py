"""
Improved NFL Playoff Predictor with Enhanced Accuracy
- Auto-detects correct season based on current date
- Weights recent games more heavily
- Adds home field advantage
- Includes turnover data
"""

import nflreadpy as nfl
import polars as pl
from datetime import datetime

def get_current_nfl_season():
    """Automatically determine the correct NFL season based on current date"""
    now = datetime.now()
    year = now.year
    month = now.month
    
    # NFL season runs Sept-Feb
    # If Jan-Feb, we're in playoffs for previous year's season
    # If March-Aug, last completed season was previous year
    # If Sept-Dec, current season
    
    if month <= 2:  # Jan-Feb (playoffs)
        season = year - 1
        phase = "Playoffs"
    elif month <= 8:  # March-Aug (offseason)
        season = year - 1
        phase = "Offseason"
    else:  # Sept-Dec (regular season)
        season = year
        phase = "Regular Season"
    
    return season, phase

def fetch_nfl_data(season=None):
    """Fetch NFL play-by-play data with EPA metrics"""
    if season is None:
        season, phase = get_current_nfl_season()
        print(f"📅 Auto-detected: {season} NFL Season ({phase})")
    
    print(f"📥 Fetching {season} NFL data...\n")
    
    try:
        pbp = nfl.load_pbp([season])
        
        # Get the actual season in the data to confirm
        actual_seasons = pbp['season'].unique().to_list()
        print(f"✓ Confirmed: Data is from season {actual_seasons[0]}")
        
        # Filter to only regular season for baseline stats
        pbp_reg = pbp.filter(pl.col('season_type') == 'REG')
        pbp_reg = pbp_reg.filter((pl.col('rush') == 1) | (pl.col('pass') == 1))
        pbp_reg = pbp_reg.to_pandas()
        
        print(f"✅ Loaded {len(pbp_reg)} regular season plays from {season} season\n")
        return pbp_reg, season
        
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def calculate_team_epa_full_season(pbp):
    """Calculate full season EPA"""
    offense = pbp.groupby('posteam')['epa'].agg(['mean', 'count']).reset_index()
    offense.columns = ['team', 'off_epa', 'off_plays']
    
    defense = pbp.groupby('defteam')['epa'].agg(['mean', 'count']).reset_index()
    defense.columns = ['team', 'def_epa', 'def_plays']
    
    team_stats = offense.merge(defense, on='team')
    return team_stats

def calculate_team_epa_recent(pbp, last_n_weeks=6):
    """Calculate EPA for recent games only (better indicator of current form)"""
    # Get max week
    max_week = pbp['week'].max()
    recent_weeks = range(max_week - last_n_weeks + 1, max_week + 1)
    
    pbp_recent = pbp[pbp['week'].isin(recent_weeks)]
    
    offense = pbp_recent.groupby('posteam')['epa'].agg(['mean', 'count']).reset_index()
    offense.columns = ['team', 'recent_off_epa', 'recent_off_plays']
    
    defense = pbp_recent.groupby('defteam')['epa'].agg(['mean', 'count']).reset_index()
    defense.columns = ['team', 'recent_def_epa', 'recent_def_plays']
    
    team_stats = offense.merge(defense, on='team')
    return team_stats

def calculate_turnovers(pbp):
    """Calculate turnover margins"""
    # Turnovers gained (on defense)
    turnovers_gained = pbp[pbp['interception'] == 1].groupby('defteam').size() + \
                       pbp[pbp['fumble_lost'] == 1].groupby('defteam').size()
    turnovers_gained = turnovers_gained.reset_index()
    turnovers_gained.columns = ['team', 'turnovers_gained']
    
    # Turnovers lost (on offense)
    turnovers_lost = pbp[pbp['interception'] == 1].groupby('posteam').size() + \
                     pbp[pbp['fumble_lost'] == 1].groupby('posteam').size()
    turnovers_lost = turnovers_lost.reset_index()
    turnovers_lost.columns = ['team', 'turnovers_lost']
    
    # Merge
    turnover_stats = turnovers_gained.merge(turnovers_lost, on='team', how='outer').fillna(0)
    turnover_stats['turnover_margin'] = turnover_stats['turnovers_gained'] - turnover_stats['turnovers_lost']
    
    return turnover_stats

def get_enhanced_team_stats(team_abbr, full_season_stats, recent_stats, turnover_stats):
    """Get comprehensive team stats"""
    full = full_season_stats[full_season_stats['team'] == team_abbr]
    recent = recent_stats[recent_stats['team'] == team_abbr]
    turnovers = turnover_stats[turnover_stats['team'] == team_abbr]
    
    if full.empty:
        return None
    
    # Weighted EPA: 40% full season, 60% recent (playoff form matters more)
    off_epa = 0.4 * float(full['off_epa'].values[0]) + 0.6 * float(recent['recent_off_epa'].values[0])
    def_epa = 0.4 * float(full['def_epa'].values[0]) + 0.6 * float(recent['recent_def_epa'].values[0])
    
    turnover_margin = float(turnovers['turnover_margin'].values[0]) if not turnovers.empty else 0
    
    return {
        'team': team_abbr,
        'off_epa': off_epa,
        'def_epa': def_epa,
        'turnover_margin': turnover_margin,
        'full_off_epa': float(full['off_epa'].values[0]),
        'full_def_epa': float(full['def_epa'].values[0]),
        'recent_off_epa': float(recent['recent_off_epa'].values[0]),
        'recent_def_epa': float(recent['recent_def_epa'].values[0]),
    }

def predict_game(team1_abbr, team2_abbr, is_team1_home, full_season_stats, recent_stats, turnover_stats, verbose=True):
    """Enhanced prediction with multiple factors"""
    team1 = get_enhanced_team_stats(team1_abbr, full_season_stats, recent_stats, turnover_stats)
    team2 = get_enhanced_team_stats(team2_abbr, full_season_stats, recent_stats, turnover_stats)
    
    if not team1 or not team2:
        return None, None
    
    # Calculate EPA differential
    off_diff = team1['off_epa'] - team2['off_epa']
    def_diff = team2['def_epa'] - team1['def_epa']  # Lower is better
    
    epa_advantage = off_diff + def_diff
    
    # Add home field advantage (worth about 0.025 EPA or ~2.5 points)
    home_advantage = 0.025 if is_team1_home else -0.025
    
    # Add turnover factor (small but meaningful)
    turnover_advantage = (team1['turnover_margin'] - team2['turnover_margin']) * 0.001
    
    # Total advantage
    total_advantage = epa_advantage + home_advantage + turnover_advantage
    
    # Convert to win probability
    win_prob = 50 + (total_advantage * 100)
    win_prob = max(20, min(80, win_prob))
    
    # Estimate point spread (EPA advantage * ~100 points = point differential)
    # Typical conversion: 0.01 EPA difference ≈ 1 point
    point_spread = total_advantage * 100
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"📊 {team1_abbr} vs {team2_abbr}" + (" (Home)" if is_team1_home else " (Away)"))
        print(f"{'='*80}")
        print(f"\n{team1_abbr} Stats:")
        print(f"  Weighted EPA: Off {team1['off_epa']:+.4f} | Def {team1['def_epa']:+.4f}")
        print(f"  Recent Form: Off {team1['recent_off_epa']:+.4f} | Def {team1['recent_def_epa']:+.4f}")
        print(f"  Turnover Margin: {team1['turnover_margin']:+.0f}")
        
        print(f"\n{team2_abbr} Stats:")
        print(f"  Weighted EPA: Off {team2['off_epa']:+.4f} | Def {team2['def_epa']:+.4f}")
        print(f"  Recent Form: Off {team2['recent_off_epa']:+.4f} | Def {team2['recent_def_epa']:+.4f}")
        print(f"  Turnover Margin: {team2['turnover_margin']:+.0f}")
        
        print(f"\n🎯 Prediction: {team1_abbr} {win_prob:.1f}% - {team2_abbr} {100-win_prob:.1f}%")
        
        if home_advantage > 0:
            print(f"   ↑ Home field advantage: +2.5% for {team1_abbr}")
        elif home_advantage < 0:
            print(f"   ↑ Home field advantage: +2.5% for {team2_abbr}")
        
        winner = team1_abbr if win_prob > 50 else team2_abbr
        winner_prob = win_prob if win_prob > 50 else (100 - win_prob)
        print(f"\n✓ Pick: {winner} ({winner_prob:.1f}%)")
        
        # Show point spread
        if point_spread > 0:
            print(f"📈 Estimated Spread: {team1_abbr} by {abs(point_spread):.1f} points")
        else:
            print(f"📈 Estimated Spread: {team2_abbr} by {abs(point_spread):.1f} points")
        
        print(f"{'='*80}\n")
    
    return team1_abbr if win_prob > 50 else team2_abbr, max(win_prob, 100 - win_prob), point_spread

def analyze_wild_card_accuracy(full_season_stats, recent_stats, turnover_stats):
    """Test accuracy against Wild Card results"""
    print("\n" + "="*80)
    print("TESTING IMPROVED MODEL ON WILD CARD WEEKEND".center(80))
    print("="*80 + "\n")
    
    # Wild Card games: (away, home, winner, score)
    games = [
        ("LA", "CAR", "LA", 34, 31),
        ("GB", "CHI", "CHI", 27, 31),  # CHI was home
        ("BUF", "JAX", "BUF", 27, 24),
        ("SF", "PHI", "SF", 23, 19),
        ("LAC", "NE", "NE", 3, 16),
        ("PIT", "HOU", "HOU", 6, 30),
    ]
    
    correct = 0
    
    for away, home, winner, away_score, home_score in games:
        predicted_winner, prob, spread = predict_game(away, home, False, full_season_stats, 
                                             recent_stats, turnover_stats, verbose=False)
        
        # Flip for home team
        if home == predicted_winner or away == predicted_winner:
            pass
        
        # Actually predict considering home field
        predicted_home, prob_home, spread_home = predict_game(home, away, True, full_season_stats,
                                                recent_stats, turnover_stats, verbose=False)
        
        predicted = predicted_home if prob_home > 50 else away
        
        was_correct = (predicted == winner)
        correct += was_correct
        
        emoji = "✅" if was_correct else "❌"
        print(f"{emoji} {away} @ {home}: Predicted {predicted} ({prob:.0f}%) | Actual: {winner} {away_score}-{home_score}")
    
    print(f"\n{'='*80}")
    print(f"IMPROVED MODEL ACCURACY: {correct}/{len(games)} ({correct/len(games)*100:.1f}%)")
    print(f"{'='*80}\n")

def main():
    """Main function"""
    print("\n" + "🏈" * 35)
    print("IMPROVED NFL PLAYOFF PREDICTOR".center(70))
    print("Enhanced with Recent Form, Home Field & Turnovers".center(70))
    print("🏈" * 35 + "\n")
    
    # Auto-detect season and fetch data
    pbp, season = fetch_nfl_data()
    
    if pbp is None:
        print("Failed to load data. Exiting.")
        return
    
    print("📊 Calculating advanced metrics...")
    full_season_stats = calculate_team_epa_full_season(pbp)
    recent_stats = calculate_team_epa_recent(pbp, last_n_weeks=6)
    turnover_stats = calculate_turnovers(pbp)
    
    print("✅ Metrics calculated\n")
    
    # Test on Wild Card games
    analyze_wild_card_accuracy(full_season_stats, recent_stats, turnover_stats)
    
    # Divisional Round Predictions
    print("\n" + "="*80)
    print("DIVISIONAL ROUND PREDICTIONS".center(80))
    print("="*80)
    
    print("\n🏈 AFC DIVISIONAL ROUND\n")
    predict_game("DEN", "BUF", True, full_season_stats, recent_stats, turnover_stats)  # DEN home
    predict_game("NE", "HOU", True, full_season_stats, recent_stats, turnover_stats)  # NE home
    
    print("\n🏈 NFC DIVISIONAL ROUND\n")
    predict_game("SEA", "SF", True, full_season_stats, recent_stats, turnover_stats)  # SEA home
    predict_game("CHI", "LA", True, full_season_stats, recent_stats, turnover_stats)  # CHI home

if __name__ == "__main__":
    main()
