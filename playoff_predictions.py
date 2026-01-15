"""
Generate predictions for 2025 NFL Wild Card Weekend matchups
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import nflreadpy as nfl
import polars as pl

# Load environment variables
load_dotenv()

# Azure OpenAI setup
endpoint = "https://foundry0012.cognitiveservices.azure.com/"
deployment = "gpt-4.1"
api_key = os.getenv("AZURE_API_KEY")
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=api_key,
)

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

def get_team_stats(team_stats, team_abbr):
    """Get stats for a specific team"""
    team_data = team_stats[team_stats['team'] == team_abbr]
    
    if team_data.empty:
        return None
    
    return {
        'team': team_abbr,
        'off_epa': float(team_data['off_epa'].values[0]),
        'def_epa': float(team_data['def_epa'].values[0]),
        'off_plays': int(team_data['off_plays'].values[0]),
        'def_plays': int(team_data['def_plays'].values[0])
    }

def analyze_matchup(team1_abbr, team2_abbr, team_stats):
    """Use AI to analyze a matchup between two teams"""
    
    team1 = get_team_stats(team_stats, team1_abbr)
    team2 = get_team_stats(team_stats, team2_abbr)
    
    if not team1 or not team2:
        return f"❌ Team not found"
    
    prompt = f"""Analyze this NFL Wild Card playoff matchup using EPA (Expected Points Added) metrics:

{team1_abbr} Stats:
- Offensive EPA/play: {team1['off_epa']:.4f}
- Defensive EPA/play: {team1['def_epa']:.4f}

{team2_abbr} Stats:
- Offensive EPA/play: {team2['off_epa']:.4f}
- Defensive EPA/play: {team2['def_epa']:.4f}

Notes:
- Offensive EPA: higher is better (more points created per play)
- Defensive EPA: lower/negative is better (fewer points allowed per play)
- Elite offense: 0.15+, Elite defense: below -0.08

Provide:
1. Brief offensive comparison (which team has advantage)
2. Brief defensive comparison (which team has advantage)
3. Win probability estimate (give a percentage for {team1_abbr})
4. One key factor that could decide the game
5. Final score prediction

Keep response under 150 words total."""

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an expert NFL analyst specializing in advanced metrics and playoff predictions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model=deployment,
        max_tokens=300,
        temperature=0.7
    )
    
    analysis = response.choices[0].message.content
    
    print("=" * 70)
    print(f"⚔️  {team1_abbr} vs {team2_abbr}")
    print("=" * 70)
    print(f"{team1_abbr}: Off EPA {team1['off_epa']:+.4f} | Def EPA {team1['def_epa']:+.4f}")
    print(f"{team2_abbr}: Off EPA {team2['off_epa']:+.4f} | Def EPA {team2['def_epa']:+.4f}")
    print("-" * 70)
    print(analysis)
    print("=" * 70 + "\n")
    
    return analysis

def main():
    """Main function to run playoff predictions"""
    
    print("\n" + "🏈" * 35)
    print("2025 NFL WILD CARD WEEKEND PREDICTIONS".center(70))
    print("Powered by EPA Metrics & AI".center(70))
    print("🏈" * 35 + "\n")
    
    pbp = fetch_nfl_data(2025)
    
    if pbp is None:
        print("Failed to load data. Exiting.")
        return
    
    team_stats = calculate_team_epa(pbp)
    
    # Wild Card Weekend Matchups
    matchups = [
        ("LAC", "HOU", "AFC"),
        ("PIT", "BAL", "AFC"),
        ("DEN", "BUF", "AFC"),
        ("GB", "PHI", "NFC"),
        ("WAS", "TB", "NFC"),
        ("MIN", "LA", "NFC"),
    ]
    
    print("=" * 70)
    print("WILD CARD WEEKEND MATCHUPS".center(70))
    print("=" * 70 + "\n")
    
    for team1, team2, conference in matchups:
        print(f"📍 {conference} Wild Card")
        analyze_matchup(team1, team2, team_stats)

if __name__ == "__main__":
    main()
