"""
Injury & Context Analyzer for NFL Predictions
Tracks:
- Key injuries (QB, WR1, OL, Edge rushers, DBs)
- Team drama/distractions
- Motivation factors
- Rest/travel
- Playoff experience
"""

def get_injury_impact():
    """
    Injury impact scores by position and player importance
    Scale: 0.00 to 0.05 EPA impact per injury
    
    In reality, you'd scrape from:
    - NFL.com injury reports
    - ESPN injury updates
    - Twitter for late-breaking news
    - Beat reporter accounts
    """
    
    injuries = {
        # Format: 'TEAM': [(player, position, impact, status)]
        
        'SF': [
            ('George Kittle', 'TE', 0.025, 'OUT'),  # Elite TE, huge loss
            ('Trent Williams', 'LT', 0.020, 'QUESTIONABLE'),  # All-Pro OL
        ],
        
        'BUF': [
            ('Josh Allen', 'QB', 0.000, 'INJURED-PLAYING'),  # Playing hurt (hand/shoulder)
            # Impact reduced since he's playing but effectiveness down
        ],
        
        'DEN': [
            # Relatively healthy
        ],
        
        'NE': [
            # Check injury reports
        ],
        
        'HOU': [
            # Check injury reports  
        ],
        
        'SEA': [
            # Check injury reports
        ],
        
        'CHI': [
            # Check injury reports
        ],
        
        'LA': [
            # Check injury reports
        ],
    }
    
    return injuries

def calculate_injury_adjustment(team):
    """
    Calculate total EPA impact from injuries
    """
    injuries = get_injury_impact()
    team_injuries = injuries.get(team, [])
    
    total_impact = 0.0
    injury_list = []
    
    for player, position, impact, status in team_injuries:
        if status in ['OUT', 'DOUBTFUL']:
            total_impact += impact
            injury_list.append(f"{player} ({position}) - {status}")
        elif status == 'QUESTIONABLE':
            # 50% chance plays at reduced effectiveness
            total_impact += impact * 0.5
            injury_list.append(f"{player} ({position}) - {status}")
        elif 'INJURED-PLAYING' in status:
            # Playing but not 100%
            total_impact += impact * 0.3
            injury_list.append(f"{player} ({position}) - Playing hurt")
    
    return total_impact, injury_list

def get_division_rivalries():
    """
    Division matchups are ALWAYS tighter than stats suggest
    - Teams know each other extremely well (2 games/year)
    - Extra motivation/intensity
    - Historical grudges
    - Coaching staff familiarity
    
    Impact: Reduces EPA advantage by ~15-20%
    """
    
    divisions = {
        'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
        'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
        'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
        'AFC West': ['DEN', 'KC', 'LV', 'LAC'],
        
        'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
        'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
        'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
        'NFC West': ['ARI', 'LA', 'SF', 'SEA'],
    }
    
    return divisions

def check_rivalry(team1, team2):
    """
    Check if two teams are division rivals
    Returns rivalry bonus and notes
    """
    divisions = get_division_rivalries()
    
    for division_name, teams in divisions.items():
        if team1 in teams and team2 in teams:
            return {
                'is_rivalry': True,
                'division': division_name,
                'epa_compression': 0.18,  # Reduces favorite's advantage by 18%
                'notes': f'{division_name} rivalry - these teams know each other very well',
                'historical': 'Played twice in regular season'
            }
    
    return {
        'is_rivalry': False,
        'division': None,
        'epa_compression': 0.0,
        'notes': 'First playoff meeting',
        'historical': None
    }

def get_team_context():
    """
    Non-injury context that affects performance
    - Coaching drama
    - Locker room issues
    - Motivation (revenge game, etc.)
    - Playoff experience
    - Recent controversies
    """
    
    context = {
        'SF': {
            'drama_penalty': 0.005,  # Kittle loss + other injuries = team morale hit
            'motivation': 0.0,
            'experience_boost': 0.010,  # Been to Super Bowl recently
            'notes': 'Multiple key injuries affecting team confidence'
        },
        
        'SEA': {
            'drama_penalty': 0.0,
            'motivation': 0.005,  # #1 seed, excited to be back in playoffs
            'experience_boost': 0.0,  # New core, less playoff experience
            'notes': 'Young team, first playoff game for many'
        },
        
        'BUF': {
            'drama_penalty': 0.0,
            'motivation': 0.010,  # Allen wants to prove himself in playoffs
            'experience_boost': 0.008,  # Been in playoffs, know what it takes
            'notes': 'Josh Allen in playoff mode, dangerous'
        },
        
        'DEN': {
            'drama_penalty': 0.0,
            'motivation': 0.005,  # Bo Nix rookie QB, chip on shoulder
            'experience_boost': 0.0,  # Young team
            'notes': 'Home field advantage crucial for young team'
        },
        
        'NE': {
            'drama_penalty': 0.0,
            'motivation': 0.008,  # Young team exceeding expectations
            'experience_boost': 0.015,  # Belichick coaching tree
            'notes': 'Playing with house money, no pressure'
        },
        
        'HOU': {
            'drama_penalty': 0.0,
            'motivation': 0.005,
            'experience_boost': 0.005,
            'notes': 'Defense playing elite football'
        },
        
        'CHI': {
            'drama_penalty': 0.0,
            'motivation': 0.008,  # Home playoff game, city excited
            'experience_boost': 0.0,  # Young team
            'notes': 'Caleb Williams in first playoff game'
        },
        
        'LA': {
            'drama_penalty': 0.0,
            'motivation': 0.005,  # Stafford wants another ring
            'experience_boost': 0.012,  # Won Super Bowl recently
            'notes': 'Championship pedigree'
        },
    }
    
    return context

def get_rest_travel_impact(team, is_home):
    """
    Rest and travel factors
    - Playoff bye week advantage
    - Cross-country travel
    - Short rest
    """
    
    bye_teams = ['DEN', 'NE', 'SEA', 'CHI']  # Had first-round bye
    
    impact = 0.0
    
    # Bye week advantage (fresh, extra prep)
    if team in bye_teams:
        impact += 0.008
    
    # Home team advantage already counted elsewhere
    # This is just for extreme travel (West Coast to East Coast)
    travel_penalty = {
        # Example: if LA had to travel to NE
    }
    
    return impact

def get_vegas_sharp_money():
    """
    Track where sharp bettors are placing money
    Line movement indicates where pros are betting
    
    In reality, scrape from:
    - Action Network
    - Covers.com
    - VSiN
    """
    
    sharp_action = {
        'BUF @ DEN': {
            'opening_line': 'DEN -2.5',
            'current_line': 'BUF -1.5',
            'movement': 'Sharp money on BUF',
            'sharp_percentage': '68% of bets on BUF',
            'analysis': 'Line moved 4 points toward Bills - sharp action'
        },
        
        'HOU @ NE': {
            'opening_line': 'NE -2',
            'current_line': 'NE -3',
            'movement': 'Line moved slightly toward NE',
            'sharp_percentage': '55% of bets on NE',
            'analysis': 'Relatively balanced'
        },
        
        'SF @ SEA': {
            'opening_line': 'SEA -8.5',
            'current_line': 'SEA -7.5',
            'movement': 'Money coming in on SF',
            'sharp_percentage': '52% on SEA',
            'analysis': 'Public likes Seahawks but sharps hedging with 49ers'
        },
        
        'LA @ CHI': {
            'opening_line': 'LA -4',
            'current_line': 'LA -3.5',
            'movement': 'Slight move toward CHI',
            'sharp_percentage': '58% on LA',
            'analysis': 'Sharps like Rams but respecting home field'
        },
    }
    
    return sharp_action

def get_altitude_factor():
    """
    Altitude impact on visiting teams
    Denver at 5,280 ft (Mile High) causes:
    - Reduced oxygen (14% less than sea level)
    - Ball travels further (less air resistance)
    - Visiting teams tire faster in 4th quarter
    - Takes 2-3 weeks to acclimate fully
    """
    altitude_impact = {
        'DEN': {
            'elevation': 5280,
            'advantage': 0.018,  # Home team advantage due to altitude
            'visitor_penalty': -0.018,  # Visitors struggle, especially late in game
            'kicking_boost': 0.005,  # Field goals/punts travel further
            'notes': 'Mile High Stadium - significant altitude advantage'
        },
        # All other stadiums near sea level
    }
    return altitude_impact

def get_weather_forecast():
    """
    Real-time weather forecasts for game day
    
    In reality, pull from:
    - Weather.gov API
    - DarkSky API
    - WeatherUnderground
    """
    
    weather = {
        'DEN': {
            'temp': 28,
            'wind': 12,
            'precip': 'Possible snow flurries',
            'impact': 'HIGH - cold + wind + ALTITUDE affects visiting teams severely',
            'epa_penalty': -0.012,
            'altitude_factor': True  # Flag for special altitude consideration
        },
        
        'NE': {
            'temp': 32,
            'wind': 8,
            'precip': 'Clear',
            'impact': 'LOW - cold but manageable',
            'epa_penalty': -0.006
        },
        
        'SEA': {
            'temp': 45,
            'wind': 10,
            'precip': '40% chance rain',
            'impact': 'LOW - typical Seattle weather',
            'epa_penalty': -0.004
        },
        
        'CHI': {
            'temp': 35,
            'wind': 15,
            'precip': 'Clear',
            'impact': 'MODERATE - wind off Lake Michigan',
            'epa_penalty': -0.008
        },
    }
    
    return weather

def get_comprehensive_analysis(team1, team2, is_home=True):
    """
    Complete context analysis for a matchup
    """
    
    # Calculate all factors
    injury_impact1, injuries1 = calculate_injury_adjustment(team1)
    injury_impact2, injuries2 = calculate_injury_adjustment(team2)
    
    context = get_team_context()
    weather = get_weather_forecast()
    altitude = get_altitude_factor()
    sharp_money = get_vegas_sharp_money()
    rivalry = check_rivalry(team1, team2)
    
    home_team = team1 if is_home else team2
    away_team = team2 if is_home else team1
    
    # Build comprehensive report
    report = {
        'matchup': f"{away_team} @ {home_team}",
        
        'injuries': {
            home_team: {
                'impact': injury_impact1 if is_home else injury_impact2,
                'key_injuries': injuries1 if is_home else injuries2
            },
            away_team: {
                'impact': injury_impact2 if is_home else injury_impact1,
                'key_injuries': injuries2 if is_home else injuries1
            }
        },
        
        'context': {
            home_team: context.get(home_team, {}),
            away_team: context.get(away_team, {})
        },
        
        'weather': weather.get(home_team, {}),
        
        'altitude': altitude.get(home_team, {}),
        
        'rivalry': rivalry,
        
        'sharp_money': sharp_money.get(f"{away_team} @ {home_team}", {}),
        
        'net_injury_advantage': injury_impact2 - injury_impact1 if is_home else injury_impact1 - injury_impact2,
    }
    
    return report

def display_context_analysis(team1, team2, is_home=True):
    """
    Display human-readable context analysis
    """
    
    analysis = get_comprehensive_analysis(team1, team2, is_home)
    home_team = team1 if is_home else team2
    away_team = team2 if is_home else team1
    
    print(f"\n{'='*90}")
    print(f"📋 CONTEXT ANALYSIS: {away_team} @ {home_team}".center(90))
    print(f"{'='*90}\n")
    
    # Injuries
    print("🏥 INJURY REPORT")
    for team in [home_team, away_team]:
        injuries = analysis['injuries'][team]['key_injuries']
        impact = analysis['injuries'][team]['impact']
        
        if injuries:
            print(f"\n   {team} (Impact: -{impact:.3f} EPA):")
            for injury in injuries:
                print(f"      • {injury}")
        else:
            print(f"\n   {team}: No significant injuries")
    
    # Altitude (if applicable)
    if analysis.get('altitude'):
        print(f"\n⛰️  ALTITUDE FACTOR ({home_team})")
        alt = analysis['altitude']
        print(f"   Elevation: {alt['elevation']:,} feet")
        print(f"   Home Advantage: +{alt['advantage']:.3f} EPA")
        print(f"   Visitor Penalty: {alt['visitor_penalty']:.3f} EPA")
        print(f"   ⚠️  {alt['notes']}")
        print(f"   💡 Total swing: ~{(alt['advantage'] - alt['visitor_penalty']) * 85:.1f} points in favor of home team")
    
    # Weather
    if analysis['weather']:
        print(f"\n🌤️  WEATHER FORECAST ({home_team})")
        w = analysis['weather']
        print(f"   Temperature: {w['temp']}°F")
        print(f"   Wind: {w['wind']} mph")
        print(f"   Conditions: {w['precip']}")
        print(f"   Impact: {w['impact']}")
    
    # Division Rivalry
    rivalry = analysis.get('rivalry', {})
    if rivalry.get('is_rivalry'):
        print(f"\n⚔️  DIVISION RIVALRY")
        print(f"   Division: {rivalry['division']}")
        print(f"   ⚠️  {rivalry['notes']}")
        print(f"   📊 EPA Compression: {rivalry['epa_compression']*100:.0f}% (games closer than stats suggest)")
        print(f"   💡 Impact: Expect a tighter game - they've played twice this season")
    else:
        print(f"\n🆕 NON-DIVISION MATCHUP")
        print(f"   {rivalry['notes']}")
        print(f"   💡 Teams less familiar with each other's schemes")
    
    # Context
    print(f"\n🎯 TEAM CONTEXT")
    for team in [home_team, away_team]:
        ctx = analysis['context'].get(team, {})
        if ctx:
            print(f"\n   {team}:")
            if ctx.get('notes'):
                print(f"      {ctx['notes']}")
            if ctx.get('experience_boost', 0) > 0:
                print(f"      ✓ Playoff experience: +{ctx['experience_boost']:.3f} EPA")
            if ctx.get('motivation', 0) > 0:
                print(f"      ✓ Motivation factor: +{ctx['motivation']:.3f} EPA")
            if ctx.get('drama_penalty', 0) > 0:
                print(f"      ⚠️  Drama penalty: -{ctx['drama_penalty']:.3f} EPA")
    
    # Sharp money
    if analysis['sharp_money']:
        print(f"\n💰 BETTING MARKET INTELLIGENCE")
        sm = analysis['sharp_money']
        print(f"   Opening Line: {sm.get('opening_line', 'N/A')}")
        print(f"   Current Line: {sm.get('current_line', 'N/A')}")
        print(f"   Line Movement: {sm.get('movement', 'N/A')}")
        print(f"   Sharp Action: {sm.get('sharp_percentage', 'N/A')}")
        print(f"   📊 Analysis: {sm.get('analysis', 'N/A')}")
    
    print(f"\n{'='*90}\n")
    
    return analysis

if __name__ == "__main__":
    """Test the analyzer"""
    print("\n" + "🔍" * 40)
    print("NFL INJURY & CONTEXT ANALYZER".center(80))
    print("🔍" * 40)
    
    # Test all divisional round games
    games = [
        ('DEN', 'BUF', True),
        ('NE', 'HOU', True),
        ('SEA', 'SF', True),
        ('CHI', 'LA', True),
    ]
    
    for home, away, is_home in games:
        display_context_analysis(home, away, is_home)
