"""Tests for tzc. Run with:  python3 -m pytest -q tests

The script has no .py extension, so it is loaded by path. Every test that
depends on "now" passes a fixed `now`, so results do not change with the date.
"""

import importlib.util
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "tzc"
_loader = SourceFileLoader("tzc", str(SCRIPT))
_spec = importlib.util.spec_from_loader("tzc", _loader)
tzc = importlib.util.module_from_spec(_spec)
_loader.exec_module(tzc)

UTC = timezone.utc
LA = ZoneInfo("America/Los_Angeles")
NOW = datetime(2026, 10, 10, 14, 0, tzinfo=UTC)


def parse(s, tz=LA, **kw):
    return tzc.parse_datetime(s, tz, now=kw.pop("now", NOW), **kw)


def utc(p):
    return p.dt.astimezone(UTC).replace(tzinfo=None)


# ---------------------------------------------------------------- local zone


def test_naive_winter_time_uses_winter_offset():
    # The original bug: a fixed "today" offset (-0700 in October) was applied
    # to January, giving 17:00 UTC instead of 18:00.
    p = parse("2026-01-15 10:00:00")
    assert utc(p) == datetime(2026, 1, 15, 18, 0)
    assert p.warnings == []


def test_naive_summer_time_uses_summer_offset():
    assert utc(parse("2026-07-15 10:00:00")) == datetime(2026, 7, 15, 17, 0)


@pytest.mark.parametrize(
    "value",
    [
        "America/Chicago",
        ":America/Chicago",
        "/usr/share/zoneinfo/America/Chicago",
        "/var/db/timezone/zoneinfo/America/Chicago",
    ],
)
def test_zone_from_name_accepts_names_and_paths(value):
    assert tzc._zone_from_name(value).key == "America/Chicago"


def test_local_tz_reads_TZ(monkeypatch):
    monkeypatch.setenv("TZ", "Asia/Tokyo")
    tz, is_iana = tzc.local_tz()
    assert is_iana and tz.key == "Asia/Tokyo"


def test_local_tz_unmappable_TZ_does_not_fall_back_to_etc_localtime(monkeypatch):
    monkeypatch.setenv("TZ", "EST5EDT,M3.2.0,M11.1.0")
    _, is_iana = tzc.local_tz()
    assert is_iana is False


# ------------------------------------------------------------- DST edges


def test_spring_forward_gap_warns_and_offers_both_readings():
    p = parse("2026-03-08 02:30:00")
    assert len(p.warnings) == 1 and "does not exist" in p.warnings[0]
    assert utc(p) == datetime(2026, 3, 8, 10, 30)  # read as PST
    label, alt = p.alternative
    assert alt.astimezone(UTC).replace(tzinfo=None) == datetime(2026, 3, 8, 9, 30)


def test_fall_back_overlap_warns_and_offers_second_occurrence():
    p = parse("2026-11-01 01:30:00")
    assert len(p.warnings) == 1 and "happened twice" in p.warnings[0]
    assert p.dt.tzname() == "PDT"
    assert utc(p) == datetime(2026, 11, 1, 8, 30)
    label, alt = p.alternative
    assert label == "2nd occurrence"
    assert alt.tzname() == "PST"
    assert alt.astimezone(UTC).replace(tzinfo=None) == datetime(2026, 11, 1, 9, 30)


def test_normal_time_on_transition_day_has_no_warning():
    p = parse("2026-11-01 12:00:00")
    assert p.warnings == [] and p.alternative is None


def test_explicit_offset_is_never_flagged_as_dst_edge():
    p = parse("2026-11-01T01:30:00-07:00")
    assert p.warnings == [] and p.alternative is None


def test_fixed_offset_default_zone_skips_dst_check():
    p = parse("2026-11-01 01:30:00", tz=timezone(timedelta(hours=-7)))
    assert p.alternative is None


# ---------------------------------------------------------- abbreviations


def test_cst_in_october_warns_about_ambiguity_and_dst_mismatch():
    p = parse("2026-10-10 14:35:00 CST")
    assert utc(p) == datetime(2026, 10, 10, 20, 35)
    text = " ".join(p.warnings)
    assert "China Standard Time" in text
    assert "CDT" in text


def test_cst_in_january_only_warns_about_ambiguity():
    p = parse("2026-01-10 14:35:00 CST")
    assert len(p.warnings) == 1 and "China" in p.warnings[0]


def test_pdt_in_october_is_clean():
    p = parse("2026-10-10 14:35:00 PDT")
    assert p.warnings == []
    assert utc(p) == datetime(2026, 10, 10, 21, 35)


def test_pst_in_july_warns_mismatch():
    p = parse("2026-07-10 14:35:00 PST")
    assert any("PDT" in w for w in p.warnings)


def test_ist_warns():
    p = parse("2026-10-10 14:35 IST")
    assert any("Israel" in w for w in p.warnings)


def test_utc_and_z_never_warn():
    assert parse("2026-10-10 14:35:00 UTC").warnings == []
    assert parse("2026-10-10T14:35:00Z").warnings == []


def test_abbreviation_does_not_eat_month_names():
    norm, used, _ = tzc.normalize_input("Mar 08 02:30:00")
    assert norm == "Mar 08 02:30:00" and used == []


# ------------------------------------------------------------- precision


def test_nanosecond_iso_keeps_microseconds():
    p = parse("2026-10-10T14:35:00.123456789Z")
    assert p.dt.microsecond == 123456
    assert any("truncated" in n for n in p.notes)


def test_millisecond_iso():
    assert parse("2026-10-10T14:35:00.250Z").dt.microsecond == 250000


@pytest.mark.parametrize(
    "value,expected_us",
    [
        ("1760106900", 0),
        ("1760106900123", 123000),
        ("1760106900123456", 123456),
        ("1760106900123456789", 123456),
        ("1760106900.5", 500000),
    ],
)
def test_epoch_resolutions_are_exact(value, expected_us):
    p = parse(value)
    assert p.dt.replace(microsecond=0) == datetime(2025, 10, 10, 14, 35, tzinfo=UTC)
    assert p.dt.microsecond == expected_us


def test_negative_epoch():
    assert parse("-1").dt == datetime(1969, 12, 31, 23, 59, 59, tzinfo=UTC)


def test_fmt_dt_and_epoch_str_show_fractions():
    dt = datetime(2026, 10, 10, 14, 35, 0, 120000, tzinfo=UTC)
    assert tzc.fmt_dt(dt).startswith("2026-10-10 14:35:00.120 ")
    assert tzc.epoch_str(dt) == "1791642900.12"
    assert tzc.epoch_str(dt.replace(microsecond=0)) == "1791642900"


# ----------------------------------------------------------- slash dates


def test_slash_date_unambiguous_day_first():
    p = parse("24/07/2026 14:35")
    assert (p.dt.month, p.dt.day) == (7, 24) and p.warnings == []


def test_slash_date_unambiguous_month_first():
    p = parse("07/24/2026 14:35:18")
    assert (p.dt.month, p.dt.day) == (7, 24) and p.warnings == []


def test_slash_date_ambiguous_defaults_to_us_and_warns():
    p = parse("03/04/2026 14:35")
    assert (p.dt.month, p.dt.day) == (3, 4)
    assert any("ambiguous" in w for w in p.warnings)


def test_slash_date_day_first_flag():
    p = parse("03/04/2026 14:35", day_first=True)
    assert (p.dt.month, p.dt.day) == (4, 3)


def test_slash_date_with_offset():
    p = parse("10/10/2026 14:35:00 +02:00")
    assert utc(p) == datetime(2026, 10, 10, 12, 35)


def test_slash_date_gets_dst_check():
    p = parse("11/01/2026 01:30")
    assert p.alternative is not None


# ------------------------------------------------------------- year-less


def test_yearless_uses_current_year_when_in_past():
    p = parse("Oct 09 10:00:00")
    assert p.dt.year == 2026


def test_yearless_in_future_rolls_back_a_year():
    p = parse("Dec 31 23:59:00")
    assert p.dt.year == 2025
    assert any("future" in n for n in p.notes)


def test_yearless_jan_first_read_on_new_years_day():
    now = datetime(2027, 1, 1, 9, 0, tzinfo=UTC)
    assert parse("Dec 31 23:59:00", now=now).dt.year == 2026


def test_yearless_feb_29_falls_back_to_leap_year():
    now = datetime(2025, 3, 1, tzinfo=UTC)
    assert parse("Feb 29 10:00:00", now=now).dt.year == 2024


# ------------------------------------------------------- existing formats


@pytest.mark.parametrize(
    "value,expected_utc",
    [
        ("2026-07-24 14:35:18", datetime(2026, 7, 24, 21, 35, 18)),
        ("2026-07-24T14:35:18+02:00", datetime(2026, 7, 24, 12, 35, 18)),
        ("24/Jul/2026:14:35:18 +0000", datetime(2026, 7, 24, 14, 35, 18)),
        ("Fri Jul 24 07:19:59 UTC 2026", datetime(2026, 7, 24, 7, 19, 59)),
        ("Fri Jul 24 07:19:59 2026", datetime(2026, 7, 24, 14, 19, 59)),
    ],
)
def test_existing_formats_still_parse(value, expected_utc):
    assert utc(parse(value)) == expected_utc


def test_relative_time():
    p = parse("2 hours, 30 minutes ago")
    assert p.dt.astimezone(UTC) == NOW - timedelta(hours=2, minutes=30)


def test_parsed_still_unpacks_as_pair():
    dt, note = parse("2026-07-24T14:35:18Z")
    assert dt.tzinfo is not None and "explicit" in note


def test_garbage_raises():
    with pytest.raises(ValueError):
        parse("not a date")


# ------------------------------------------------------------------- CLI


def run_cli(*args, tz="America/Los_Angeles"):
    env = dict(os.environ, TZ=tz, NO_COLOR="1")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--no-color", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_cli_shows_both_readings_for_overlap():
    r = run_cli("--to", "UTC", "2026-11-01 01:30:00")
    assert r.returncode == 0
    assert "2026-11-01 08:30:00 UTC" in r.stdout
    assert "2026-11-01 09:30:00 UTC" in r.stdout
    assert "!!" in r.stdout


def test_cli_strict_exit_code():
    assert run_cli("--strict", "--to", "UTC", "2026-11-01 01:30:00").returncode == 3
    assert run_cli("--strict", "--to", "UTC", "2026-11-01 12:00:00").returncode == 0


def test_cli_bad_from_zone_is_a_clean_error():
    r = run_cli("--from", "Not/AZone", "--to", "UTC", "2026-01-01 00:00:00")
    assert r.returncode == 1 and "Unknown timezone" in r.stderr
    assert "Traceback" not in r.stderr


def test_cli_unmappable_TZ_warns():
    r = run_cli("--to", "UTC", "2026-01-15 10:00:00", tz="EST5EDT,M3.2.0,M11.1.0")
    assert "Could not determine your IANA timezone" in r.stdout
