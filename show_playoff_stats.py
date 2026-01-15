"""
Show EPA stats for 2025 NFL Playoff teams
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
    team_stats = team_stats.sort_values('off_epa', ascending=False)
    
    return team_stats

def main():
    """Main function to show playoff team stats"""
    
    print("\n" + "🏈" * 35)
    print("2025 NFL PLAYOFF TEAM EPA RANKINGS".center(70))
    print("🏈" * 35 + "\n")
    
    pbp = fetch_nfl_data(2025)
    
    if pbp is None:
        print("Failed to load data. Exiting.")
        return
    
    team_stats = calculate_team_epa(pbp)
    
    # Playoff teams
    playoff_teams = ['KC', 'BUF', 'BAL', 'HOU', 'LAC', 'PIT', 'DEN',  # AFC
                     'PHI', 'DET', 'TB', 'LA', 'MIN', 'GB', 'WAS']    # NFC
    
    playoff_stats = team_stats[team_stats['team'].isin(playoff_teams)].copy()
    
    print("=" * 90)
    print("ALL PLAYOFF TEAMS - EPA RANKINGS".center(90))
    print("=" * 90)
    print(f"{'Team':<6} {'Off EPA':<12} {'Def EPA':<12} {'Off Rank':<12} {'Def Rank':<12}")
    print("-" * 90)
    
    # Add rankings
    team_stats['off_rank'] = team_stats['off_epa'].rank(ascending=False).astype(int)
    team_stats['def_rank'] = team_stats['def_epa'].rank(ascending=True).astype(int)
    
    for _, row in playoff_stats.iterrows():
        off_rank = team_stats[team_stats['team'] == row['team']]['off_rank'].values[0]
        def_rank = team_stats[team_stats['team'] == row['team']]['def_rank'].values[0]
        
        print(f"{row['team']:<6} {row['off_epa']:+.4f} ({off_rank}/32)   {row['def_epa']:+.4f} ({def_rank}/32)")
    
    # Wild Card Matchups
    print("\n" + "=" * 90)
    print("WILD CARD WEEKEND MATCHUPS".center(90))
    print("=" * 90 + "\n")
    
    matchups = [
        ("LAC", "HOU", "AFC"),
        ("PIT", "BAL", "AFC"),
        ("DEN", "BUF", "AFC"),
        ("GB", "PHI", "NFC"),
        ("WAS", "TB", "NFC"),
        ("MIN", "LA", "NFC"),
    ]
    
    for team1, team2, conf in matchups:
        t1_stats = playoff_stats[playoff_stats['team'] == team1].iloc[0]
        t2_stats = playoff_stats[playoff_stats['team'] == team2].iloc[0]
        
        print(f"📍 {conf} Wild Card: {team1} vs {team2}")
        print("-" * 90)
        print(f"{team1}: Off EPA {t1_stats['off_epa']:+.4f} | Def EPA {t1_stats['def_epa']:+.4f}")
        print(f"{team2}: Off EPA {t2_stats['off_epa']:+.4f} | Def EPA {t2_stats['def_epa']:+.4f}")
        
        # Simple analysis
        off_adv = team1 if t1_stats['off_epa'] > t2_stats['off_epa'] else team2
        def_adv = team1 if t1_stats['def_epa'] < t2_stats['def_epa'] else team2
        
        print(f"\n💡 Quick Analysis:")
        print(f"   Offensive advantage: {off_adv}")
        print(f"   Defensive advantage: {def_adv}")
        
        # Calculate simple win probability based on EPA
        epa_diff = (t1_stats['off_epa'] - t2_stats['off_epa']) + (t2_stats['def_epa'] - t1_stats['def_epa'])
        win_prob = 50 + (epa_diff * 100)
        win_prob = max(20, min(80, win_prob))  # Cap between 20-80%
        
        print(f"   Win probability: {team1} {win_prob:.0f}% - {team2} {100-win_prob:.0f}%")
        print("=" * 90 + "\n")

if __name__ == "__main__":
    main()
