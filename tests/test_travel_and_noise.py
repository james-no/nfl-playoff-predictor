import math
from utils.travel import timezone_diff, compute_travel_penalty, compute_fan_noise_boost
from config import TeamsConfig, BettingConfig, TravelConfig


def test_timezone_diff_coast_to_coast():
    # SEA (PT) at BUF (ET) = 3 zones
    assert timezone_diff('BUF', 'SEA') == 3


def test_travel_penalty_short_week_scaling():
    # PT -> ET (3 zones) base = -0.018; short week multiplier 1.5 => -0.027
    pen = compute_travel_penalty('BUF', 'SEA', away_rest_days=6)
    assert math.isclose(pen, TravelConfig.TZ_DIFF_PENALTY[3] * TravelConfig.SHORT_WEEK_MULTIPLIER, rel_tol=1e-9)


def test_fan_noise_boost_loud_vs_non_loud():
    # SEA is loud, not dome
    boost_sea = compute_fan_noise_boost('SEA')
    assert math.isclose(
        boost_sea,
        BettingConfig.FAN_NOISE_BASE_EPA + BettingConfig.FAN_NOISE_LOUD_STADIUM_BONUS_EPA,
        rel_tol=1e-9,
    )

    # CAR is not in loud list and not a dome
    boost_car = compute_fan_noise_boost('CAR')
    assert math.isclose(boost_car, BettingConfig.FAN_NOISE_BASE_EPA, rel_tol=1e-9)
