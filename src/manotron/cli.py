from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from manotron.config import config_path, default_settings, load_settings, save_settings
from manotron.db import init_db
from manotron.export import export_configured
from manotron.openai_client import validate_api_key
from manotron.scan import scan_configured_folder
from manotron.schedule import (
    clear_scan_cron,
    cron_for_daily,
    cron_for_every_hours,
    cron_for_weekdays,
    cron_for_weekly,
    current_scan_cron,
    install_scan_cron,
)
from manotron.schemas import ExportOptions

app = typer.Typer(
    help="Turn invoice scans into structured SQLite rows and Excel exports.",
    no_args_is_help=True,
)
schedule_app = typer.Typer(
    help="Manage automatic recursive scans.",
    no_args_is_help=True,
)
config_app = typer.Typer(
    help="View or change local settings.",
    no_args_is_help=True,
)
app.add_typer(schedule_app, name="schedule")
app.add_typer(config_app, name="config")


@app.command()
def init(
    folder: Annotated[Path | None, typer.Option(help="Folder to scan recursively.")] = None,
    api_key: Annotated[str | None, typer.Option(help="OpenAI API key to store.")] = None,
    model: Annotated[str, typer.Option(help="OpenAI model used for extraction.")] = "gpt-5-mini",
    export_folder: Annotated[Path | None, typer.Option(help="Default Excel export folder.")] = None,
    skip_key_validation: Annotated[
        bool,
        typer.Option(help="Store the key without calling OpenAI first."),
    ] = False,
) -> None:
    """Create the local config and SQLite database."""
    settings = load_settings() if config_path().exists() else default_settings()
    if folder:
        settings.watch_folder = str(folder.expanduser().resolve())
    if api_key:
        if not skip_key_validation:
            _validate_api_key_or_exit(api_key)
        settings.openai_api_key = api_key
    settings.openai_model = model
    if export_folder:
        settings.export_default_folder = str(export_folder.expanduser().resolve())

    init_db(settings.db_path)
    path = save_settings(settings)
    typer.echo(f"Config saved: {path}")
    typer.echo(f"SQLite DB: {settings.db_path}")


@app.command("validate-key")
def validate_key(
    api_key: Annotated[str | None, typer.Option(help="OpenAI API key. Uses config/env if omitted.")] = None,
) -> None:
    """Check an OpenAI API key without running extraction."""
    settings = default_settings() if api_key else load_settings()
    key = api_key or settings.openai_api_key
    if not key:
        raise typer.BadParameter("No API key provided and none exists in config or OPENAI_API_KEY.")
    _validate_api_key_or_exit(key)
    typer.echo("OpenAI API key is valid.")


@app.command()
def scan(
    mock_extract: Annotated[
        bool,
        typer.Option("--mock-extract", help="Use deterministic local extraction for testing."),
    ] = False,
) -> None:
    """Recursively process new supported files in the configured folder."""
    summary = scan_configured_folder(mock_extract=mock_extract)
    typer.echo(
        "Scan complete: "
        f"seen={summary.files_seen}, "
        f"processed={summary.files_processed}, "
        f"skipped={summary.files_skipped}, "
        f"failed={summary.files_failed}"
    )


@app.command()
def export(
    output: Annotated[Path | None, typer.Option("--out", "-o", help="Excel output path.")] = None,
    date_from: Annotated[str | None, typer.Option("--from", help="Invoice date from YYYY-MM-DD.")] = None,
    date_to: Annotated[str | None, typer.Option("--to", help="Invoice date to YYYY-MM-DD.")] = None,
) -> None:
    """Export stored invoice lines to an Excel workbook."""
    path = export_configured(ExportOptions(output_path=output, date_from=date_from, date_to=date_to))
    typer.echo(f"Exported: {path}")


@config_app.command("show")
def config_show() -> None:
    """Show local settings with the API key hidden."""
    settings = load_settings()
    redacted = settings.model_copy()
    if redacted.openai_api_key:
        redacted.openai_api_key = "***"
    typer.echo(redacted.model_dump_json(indent=2))


@config_app.command("set-folder")
def config_set_folder(folder: Path) -> None:
    """Change the folder scanned by manotron."""
    settings = load_settings()
    settings.watch_folder = str(folder.expanduser().resolve())
    save_settings(settings)
    typer.echo(f"Watch folder: {settings.watch_folder}")


@config_app.command("set-model")
def config_set_model(model: str) -> None:
    """Change the OpenAI extraction model."""
    settings = load_settings()
    settings.openai_model = model
    save_settings(settings)
    typer.echo(f"OpenAI model: {settings.openai_model}")


@schedule_app.command("set")
def schedule_set(
    daily: Annotated[str | None, typer.Option(help="Run every day at HH:MM.")] = None,
    weekdays: Annotated[str | None, typer.Option(help="Run Monday-Friday at HH:MM.")] = None,
    weekly_day: Annotated[str | None, typer.Option(help="Run weekly on day: mon/tue/...")] = None,
    weekly_time: Annotated[str | None, typer.Option(help="Weekly run time HH:MM.")] = None,
    every_hours: Annotated[int | None, typer.Option(help="Run every N hours, 1-23.")] = None,
    command: Annotated[str | None, typer.Option(help="Command cron should execute.")] = None,
) -> None:
    """Install or replace the automatic scan schedule."""
    selected = [daily is not None, weekdays is not None, every_hours is not None, weekly_day is not None]
    if sum(selected) != 1:
        raise typer.BadParameter("Choose exactly one schedule option.")
    if daily:
        expression = cron_for_daily(daily)
    elif weekdays:
        expression = cron_for_weekdays(weekdays)
    elif every_hours is not None:
        expression = cron_for_every_hours(every_hours)
    else:
        if not weekly_day or not weekly_time:
            raise typer.BadParameter("Weekly schedule needs --weekly-day and --weekly-time.")
        expression = cron_for_weekly(weekly_day, weekly_time)

    entry = install_scan_cron(expression, command=command)
    typer.echo(f"Installed cron: {entry}")


@schedule_app.command("clear")
def schedule_clear() -> None:
    """Remove the automatic scan schedule."""
    clear_scan_cron()
    typer.echo("Removed manotron cron entry.")


@schedule_app.command("show")
def schedule_show() -> None:
    """Show the current automatic scan schedule."""
    entry = current_scan_cron()
    typer.echo(entry or "No manotron cron entry installed.")


def _validate_api_key_or_exit(api_key: str) -> None:
    try:
        validate_api_key(api_key)
    except Exception:
        raise typer.BadParameter("OpenAI rejected this API key.")
