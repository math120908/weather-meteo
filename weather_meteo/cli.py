from __future__ import annotations

import click

from weather_meteo.api import get_backend
from weather_meteo.config import Config, load_config, save_config, edit_config, CONFIG_FILE
from weather_meteo.formatters import get_formatter
from weather_meteo.location import detect_current_location, geocode_search, resolve_location
from weather_meteo.models import FORECAST_MODELS


def _fetch_multi_model_hourly(
    config: Config,
    loc,
    models: list[str],
    hours: int = 24,
) -> dict[str, list]:
    """Fetch hourly data from multiple models. Returns {model_name: [HourlyEntry]}."""
    result = {}
    for model_name in models:
        backend = get_backend(config.backend, config.unit, model_name)
        result[model_name] = backend.get_hourly(loc, hours=hours)
    return result


def _resolve(ctx: click.Context, loc_name: str | None = None) -> tuple:
    config = ctx.obj["config"]
    fmt_name = ctx.obj["format"] or config.format
    formatter = get_formatter(fmt_name)
    # Per-location model override > global default
    model = config.model
    if loc_name and loc_name in config.locations:
        loc_model = config.locations[loc_name].model
        if loc_model:
            model = loc_model
    elif config.default_location in config.locations:
        loc_model = config.locations[config.default_location].model
        if loc_model:
            model = loc_model
    backend = get_backend(config.backend, config.unit, model)
    return config, formatter, backend


@click.group(invoke_without_command=True)
@click.option("--location", "-l", default=None, help="Location alias or city name.")
@click.option("--format", "-f", "fmt", default=None, type=click.Choice(["ascii", "emoji", "json"]), help="Output format.")
@click.option("--model", "-m", default=None, help="Forecast model (overrides config).")
@click.option("--list-models", is_flag=True, help="List available forecast models.")
@click.option("--full", is_flag=True, help="Show extended weather data (humidity, UV, pressure, etc.).")
@click.pass_context
def main(
    ctx: click.Context,
    location: str | None,
    fmt: str | None,
    model: str | None,
    list_models: bool,
    full: bool,
) -> None:
    """Weather CLI powered by Open-Meteo."""
    if list_models:
        click.echo("Available forecast models:\n")
        for model_id, desc in FORECAST_MODELS:
            click.echo(f"  {model_id:<35} {desc}")
        click.echo("\nSet globally: defaults.model in config")
        click.echo("Set per-location: locations.<alias>.model in config")
        click.echo("Override: weather-meteo --model <id> ...")
        ctx.exit()
        return
    ctx.ensure_object(dict)
    config = load_config()
    models: list[str] = []
    if model:
        models = [m.strip() for m in model.split(",")]
        config.model = models[0]
    ctx.obj["config"] = config
    ctx.obj["location"] = location
    ctx.obj["format"] = fmt
    ctx.obj["models"] = models
    ctx.obj["full"] = full
    if ctx.invoked_subcommand is None:
        ctx.invoke(hourly)


@main.command()
@click.option("--hours", "-H", default=24, help="Hours to show (default 24).")
@click.pass_context
def hourly(ctx: click.Context, hours: int) -> None:
    """Hourly forecast (default command)."""
    full = ctx.obj.get("full", False)
    models = ctx.obj.get("models", [])
    config, formatter, backend = _resolve(ctx, ctx.obj["location"])
    loc = resolve_location(ctx.obj["location"], config)
    if len(models) > 1:
        model_data = _fetch_multi_model_hourly(config, loc, models, hours=hours)
        click.echo(formatter.format_model_compare(model_data, loc.label, unit=config.unit, hours=hours))
    else:
        entries = backend.get_hourly(loc, hours=hours, full=full)
        click.echo(formatter.format_hourly(entries, loc.label, title=f"Next {hours}h", unit=config.unit))


@main.command()
@click.option("--detail", is_flag=True, help="Show full hourly breakdown per day.")
@click.pass_context
def week(ctx: click.Context, detail: bool) -> None:
    """7-day forecast with rain heatmap."""
    full = ctx.obj.get("full", False)
    config, formatter, backend = _resolve(ctx, ctx.obj["location"])
    loc = resolve_location(ctx.obj["location"], config)
    daily = backend.get_daily(loc, days=7, detail=detail, full=full)
    click.echo(formatter.format_week(daily, loc.label, unit=config.unit, detail=detail))


@main.command()
@click.argument("locations", nargs=-1, required=True)
@click.pass_context
def compare(ctx: click.Context, locations: tuple[str, ...]) -> None:
    """Compare weather across multiple locations."""
    config = ctx.obj["config"]
    fmt_name = ctx.obj["format"] or config.format
    formatter = get_formatter(fmt_name)
    currents = []
    for loc_name in locations:
        _, _, backend = _resolve(ctx, loc_name)
        loc = resolve_location(loc_name, config)
        current = backend.get_current(loc)
        current.location_label = loc.label
        currents.append(current)
    click.echo(formatter.format_compare(currents, unit=config.unit))


@main.command()
@click.option("--date", "-d", "target_date", required=True, type=click.DateTime(formats=["%Y-%m-%d"]), help="Date to query (YYYY-MM-DD).")
@click.pass_context
def history(ctx: click.Context, target_date) -> None:
    """Historical weather for a past date."""
    full = ctx.obj.get("full", False)
    config, formatter, backend = _resolve(ctx, ctx.obj["location"])
    loc = resolve_location(ctx.obj["location"], config)
    d = target_date.date() if hasattr(target_date, "date") else target_date
    entries = backend.get_history(loc, d, full=full)
    click.echo(formatter.format_hourly(
        entries,
        loc.label,
        title=f"{d.isoformat()} (historical)",
        unit=config.unit,
    ))


@main.group()
def config_cmd() -> None:
    """Manage configuration."""


# Register config_cmd as "config" subcommand
main.add_command(config_cmd, "config")


@config_cmd.command()
def setup() -> None:
    """Interactive first-time setup."""
    click.echo("Detecting your location...")
    try:
        detected = detect_current_location()
        click.echo(f"Detected location: {detected.label} ({detected.lat}, {detected.lon})")
        use_it = click.confirm("Use as default?", default=True)
    except Exception:
        click.echo("Could not auto-detect location.")
        use_it = False
        detected = None

    if use_it and detected:
        alias = click.prompt("Alias name", default=detected.label.split(",")[0].strip().lower())
    else:
        name = click.prompt("Enter location name")
        from weather_meteo.location import _geocode
        detected = _geocode(name)
        click.echo(f"Found: {detected.label} ({detected.lat}, {detected.lon})")
        alias = click.prompt("Alias name", default=name.lower().replace(" ", "-"))

    unit = click.prompt(
        "Unit system",
        type=click.Choice(["metric", "imperial"]),
        default="metric",
    )
    fmt = click.prompt(
        "Default format",
        type=click.Choice(["ascii", "emoji", "json"]),
        default="ascii",
    )
    cfg = Config(
        default_location=alias,
        unit=unit,
        format=fmt,
        locations={alias: detected},
    )
    save_config(cfg)
    click.echo(f"Config saved to {CONFIG_FILE}")


@config_cmd.command()
@click.option("--name", "-n", required=True, help="Alias for this location.")
@click.argument("query")
def add(name: str, query: str) -> None:
    """Add a location by searching. Example: config add --name home "dublin 2" """
    config = load_config()

    # Check for existing alias
    if name in config.locations:
        existing = config.locations[name]
        if not click.confirm(
            f"'{name}' already exists ({existing.label}). Overwrite?",
            default=False,
        ):
            click.echo("Aborted.")
            return

    # Search for locations
    click.echo(f"Searching for '{query}'...")
    results = geocode_search(query, count=5)
    if not results:
        raise click.ClickException(f"No locations found for: {query!r}")

    # Display results
    click.echo()
    for i, loc in enumerate(results, 1):
        map_url = f"https://www.google.com/maps?q={loc.lat},{loc.lon}"
        click.echo(f"  [{i}] {loc.label} ({loc.lat}, {loc.lon})")
        click.echo(f"      {map_url}")
    click.echo()

    # Prompt for selection
    choice = click.prompt(
        "Select",
        type=click.IntRange(1, len(results)),
        default=1,
    )
    selected = results[choice - 1]

    # Save
    config.locations[name] = selected
    save_config(config)
    click.echo(f"Added '{name}' -> {selected.label} ({selected.lat}, {selected.lon})")


@config_cmd.command()
def edit() -> None:
    """Open config in $EDITOR."""
    edit_config()


@config_cmd.command()
def show() -> None:
    """Print current config."""
    if not CONFIG_FILE.exists():
        click.echo("No config file found. Run 'weather-meteo config setup' first.")
        return
    click.echo(CONFIG_FILE.read_text())
