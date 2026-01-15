"""
Show EPA stats for all 2025 NFL Playoff teams
"""

import nflreadpy as nfl
import polars as pl

def fetch_nfl_data(season=2024):
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
    
    # Add rankings
    team_stats['off_rank'] = team_stats['off_epa'].rank(ascending=False).astype(int)
    team_stats['def_rank'] = team_stats['def_epa'].rank(ascending=True).astype(int)
    
    team_stats = team_stats.sort_values('off_epa', ascending=False)
    
    return team_stats

def main():
    """Main function to show playoff team stats"""
    
    print("\n" + "🏈" * 35)
    print("2024 NFL PLAYOFF TEAMS - EPA STATS".center(70))
    print("🏈" * 35 + "\n")
    
    pbp = fetch_nfl_data(2025)
    
    if pbp is None:
        print("Failed to load data. Exiting.")
        return
    
    team_stats = calculate_team_epa(pbp)
    
    # AFC Playoff teams
    print("=" * 100)
    print("AFC PLAYOFF TEAMS".center(100))
    print("=" * 100)
    print(f"{'Team':<8} {'Off EPA':<12} {'Off Rank':<12} {'Def EPA':<12} {'Def Rank':<12} {'Notes'}")
    print("-" * 100)
    
    afc_teams = ['DEN', 'NE', 'JAX', 'PIT', 'HOU', 'BUF', 'LAC']
    
    for team in afc_teams:
        row = team_stats[team_stats['team'] == team].iloc[0]
        seed = ""
        if team == 'DEN': seed = "#1 seed (bye)"
        elif team == 'NE': seed = "#2 seed"
        
        print(f"{team:<8} {row['off_epa']:+.4f} ({row['off_rank']}/32)  {row['def_epa']:+.4f} ({row['def_rank']}/32)  {seed}")
    
    # NFC Playoff teams
    print("\n" + "=" * 100)
    print("NFC PLAYOFF TEAMS".center(100))
    print("=" * 100)
    print(f"{'Team':<8} {'Off EPA':<12} {'Off Rank':<12} {'Def EPA':<12} {'Def Rank':<12} {'Notes'}")
    print("-" * 100)
    
    nfc_teams = ['SEA', 'CHI', 'CAR', 'LA', 'SF', 'GB', 'PHI']
    
    for team in nfc_teams:
        row = team_stats[team_stats['team'] == team].iloc[0]
        seed = ""
        if team == 'SEA': seed = "#1 seed (bye)"
        elif team == 'CHI': seed = "#2 seed"
        
        print(f"{team:<8} {row['off_epa']:+.4f} ({row['off_rank']}/32)  {row['def_epa']:+.4f} ({row['def_rank']}/32)  {seed}")
    
    print("\n" + "=" * 100)
    print("NOTES:")
    print("- Offensive EPA: Higher is better (more points created per play)")
    print("- Defensive EPA: Lower/negative is better (fewer points allowed per play)")
    print("- Elite offense: +0.15 or higher | Elite defense: -0.08 or lower")
    print("=" * 100)

if __name__ == "__main__":
    main()
