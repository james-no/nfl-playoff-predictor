"""
NFL Playoff Predictor
Uses EPA (Expected Points Added) metrics and AI analysis to predict playoff matchups
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
    print(f"📥 Fetching {season} NFL data...")
    
    try:
        # Load play-by-play data using nflreadpy
        pbp = nfl.load_pbp([season])
        
        # Filter to only rush and pass plays (real plays, not penalties/timeouts)
        # nflreadpy uses Polars, not pandas - use .filter() instead of boolean indexing
        pbp = pbp.filter((pl.col('rush') == 1) | (pl.col('pass') == 1))
        
        # Filter to regular season only
        pbp = pbp.filter(pl.col('season_type') == 'REG')
        
        # Convert to pandas for easier processing
        pbp = pbp.to_pandas()
        
        print(f"✅ Loaded {len(pbp)} plays from {season} season\n")
        return pbp
        
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def calculate_team_epa(pbp):
    """Calculate offensive and defensive EPA for all teams"""
    
    # Offensive EPA (higher is better)
    offense = pbp.groupby('posteam')['epa'].agg(['mean', 'count']).reset_index()
    offense.columns = ['team', 'off_epa', 'off_plays']
    
    # Defensive EPA (lower is better - negative means preventing points)
    defense = pbp.groupby('defteam')['epa'].agg(['mean', 'count']).reset_index()
    defense.columns = ['team', 'def_epa', 'def_plays']
    
    # Merge offense and defense
    team_stats = offense.merge(defense, on='team')
    
    # Sort by offensive EPA
    team_stats = team_stats.sort_values('off_epa', ascending=False)
    
    return team_stats


def display_top_teams(team_stats, top_n=10):
    """Display top offensive and defensive teams"""
    
    print("=" * 60)
    print(f"📊 TOP {top_n} OFFENSES (EPA per play)")
    print("=" * 60)
    
    top_offense = team_stats.nlargest(top_n, 'off_epa')
    for idx, row in enumerate(top_offense.itertuples(), 1):
        print(f"{idx:2d}. {row.team:3s}  |  {row.off_epa:+.4f} EPA/play")
    
    print("\n" + "=" * 60)
    print(f"🛡️  TOP {top_n} DEFENSES (EPA per play)")
    print("=" * 60)
    
    top_defense = team_stats.nsmallest(top_n, 'def_epa')
    for idx, row in enumerate(top_defense.itertuples(), 1):
        print(f"{idx:2d}. {row.team:3s}  |  {row.def_epa:+.4f} EPA/play")
    
    print("\n")


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
    
    # Get team stats
    team1 = get_team_stats(team_stats, team1_abbr)
    team2 = get_team_stats(team_stats, team2_abbr)
    
    if not team1:
        return f"❌ Team '{team1_abbr}' not found. Check abbreviation."
    if not team2:
        return f"❌ Team '{team2_abbr}' not found. Check abbreviation."
    
    # Create analysis prompt
    prompt = f"""Analyze this NFL playoff matchup using EPA (Expected Points Added) metrics:

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
3. Win probability estimate (give a percentage)
4. One key factor that could decide the game
5. Betting insight (1-2 sentences)

Keep response under 150 words total."""

    # Get AI analysis
    print(f"\n🤔 Analyzing {team1_abbr} vs {team2_abbr}...\n")
    
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
    
    # Display results
    print("=" * 60)
    print(f"⚔️  MATCHUP ANALYSIS: {team1_abbr} vs {team2_abbr}")
    print("=" * 60)
    print(analysis)
    print("=" * 60 + "\n")
    
    return analysis


def main():
    """Main function to run the NFL predictor"""
    
    print("\n" + "🏈" * 30)
    print("NFL PLAYOFF PREDICTOR".center(60))
    print("Powered by EPA Metrics & AI".center(60))
    print("🏈" * 30 + "\n")
    
    # Fetch data
    pbp = fetch_nfl_data(2025)
    
    if pbp is None:
        print("Failed to load data. Exiting.")
        return
    
    # Calculate team stats
    team_stats = calculate_team_epa(pbp)
    
    # Display top teams
    display_top_teams(team_stats, top_n=10)
    
    # Interactive matchup analysis
    print("=" * 60)
    print("ANALYZE MATCHUPS")
    print("=" * 60)
    print("Enter team matchups to analyze (e.g., 'KC vs BUF')")
    print("Type 'teams' to see all team abbreviations")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("Enter matchup: ").strip()
        
        if user_input.lower() == 'quit':
            print("\n👋 Thanks for using NFL Playoff Predictor!")
            break
        
        if user_input.lower() == 'teams':
            print("\nAvailable teams:")
            for team in sorted(team_stats['team'].unique()):
                print(f"  {team}")
            print()
            continue
        
        # Parse matchup
        if ' vs ' in user_input.lower():
            parts = user_input.replace(' vs ', ',').replace(' VS ', ',').split(',')
            if len(parts) == 2:
                team1 = parts[0].strip().upper()
                team2 = parts[1].strip().upper()
                analyze_matchup(team1, team2, team_stats)
            else:
                print("❌ Invalid format. Use: TEAM1 vs TEAM2\n")
        else:
            print("❌ Invalid format. Use: TEAM1 vs TEAM2 (e.g., 'KC vs BUF')\n")


if __name__ == "__main__":
    main()
