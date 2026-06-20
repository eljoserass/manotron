from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from manotron.config import log_dir

BEGIN_MARKER = "# manotron scan start"
END_MARKER = "# manotron scan end"
WEEKDAYS = {
    "sun": "0",
    "mon": "1",
    "tue": "2",
    "wed": "3",
    "thu": "4",
    "fri": "5",
    "sat": "6",
}


def cron_for_daily(time_24h: str) -> str:
    hour, minute = _parse_time(time_24h)
    return f"{minute} {hour} * * *"


def cron_for_weekdays(time_24h: str) -> str:
    hour, minute = _parse_time(time_24h)
    return f"{minute} {hour} * * 1-5"


def cron_for_weekly(day: str, time_24h: str) -> str:
    hour, minute = _parse_time(time_24h)
    key = day.strip().lower()[:3]
    if key not in WEEKDAYS:
        raise ValueError("Weekly day must be one of: sun, mon, tue, wed, thu, fri, sat.")
    return f"{minute} {hour} * * {WEEKDAYS[key]}"


def cron_for_every_hours(hours: int) -> str:
    if hours < 1 or hours > 23:
        raise ValueError("Hours must be between 1 and 23.")
    return f"0 */{hours} * * *"


def install_scan_cron(cron_expression: str, command: str | None = None) -> str:
    scan_command = command or default_scan_command()
    log_path = log_dir() / "scan.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = f"{cron_expression} {scan_command} >> {log_path} 2>&1"
    new_crontab = _replace_manotron_block(_read_crontab(), [BEGIN_MARKER, entry, END_MARKER])
    _write_crontab(new_crontab)
    return entry


def clear_scan_cron() -> None:
    _write_crontab(_replace_manotron_block(_read_crontab(), []))


def current_scan_cron() -> str | None:
    lines = _extract_block(_read_crontab())
    return "\n".join(lines) if lines else None


def default_scan_command() -> str:
    executable = shutil.which("manotron")
    if executable:
        return f"{executable} scan"
    return f"{sys.executable} -m manotron scan"


def _parse_time(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", value.strip())
    if not match:
        raise ValueError("Time must use 24-hour HH:MM format, for example 21:30.")
    return int(match.group(1)), int(match.group(2))


def _read_crontab() -> list[str]:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def _write_crontab(lines: list[str]) -> None:
    with tempfile.NamedTemporaryFile("w", delete=False) as file:
        file.write("\n".join(lines).rstrip() + ("\n" if lines else ""))
        temp_path = Path(file.name)
    try:
        subprocess.run(["crontab", str(temp_path)], check=True)
    finally:
        temp_path.unlink(missing_ok=True)


def _replace_manotron_block(lines: list[str], replacement: list[str]) -> list[str]:
    output: list[str] = []
    in_block = False
    inserted = False
    for line in lines:
        if line.strip() == BEGIN_MARKER:
            in_block = True
            if replacement and not inserted:
                output.extend(replacement)
                inserted = True
            continue
        if line.strip() == END_MARKER:
            in_block = False
            continue
        if not in_block:
            output.append(line)
    if replacement and not inserted:
        if output and output[-1].strip():
            output.append("")
        output.extend(replacement)
    return output


def _extract_block(lines: list[str]) -> list[str]:
    found: list[str] = []
    in_block = False
    for line in lines:
        if line.strip() == BEGIN_MARKER:
            in_block = True
            continue
        if line.strip() == END_MARKER:
            break
        if in_block:
            found.append(line)
    return found

