from manotron.schedule import (
    cron_for_daily,
    cron_for_every_hours,
    cron_for_weekdays,
    cron_for_weekly,
)


def test_cron_expressions() -> None:
    assert cron_for_daily("21:30") == "30 21 * * *"
    assert cron_for_weekdays("08:05") == "5 8 * * 1-5"
    assert cron_for_weekly("mon", "07:00") == "0 7 * * 1"
    assert cron_for_every_hours(6) == "0 */6 * * *"

