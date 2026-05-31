import click


@click.group(invoke_without_command=True)
@click.option("--location", "-l", default=None, help="Location alias or city name.")
@click.option("--format", "-f", "fmt", default=None, type=click.Choice(["ascii", "emoji", "json"]), help="Output format.")
@click.pass_context
def main(ctx: click.Context, location: str | None, fmt: str | None) -> None:
    """Weather CLI powered by Open-Meteo."""
    ctx.ensure_object(dict)
    ctx.obj["location"] = location
    ctx.obj["format"] = fmt
    if ctx.invoked_subcommand is None:
        click.echo("weather-meteo: use --help for usage, or run 'config setup' first.")
