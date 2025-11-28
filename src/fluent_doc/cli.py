"""CLI for Fluent documentation lookup."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional

from .core import FluentDocFetcher, THEORY_URLS, SECTION_NAMES, fetch_section

app = typer.Typer(help="Fluent documentation lookup tool")
console = Console()


@app.command()
def sections():
    """List available pre-defined theory sections."""
    table = Table(title="Available Theory Sections")
    table.add_column("Key", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("URL Path", style="dim")

    for key in THEORY_URLS:
        table.add_row(key, SECTION_NAMES.get(key, key), THEORY_URLS[key])

    console.print(table)


@app.command()
def theory(
    section: str = typer.Argument(..., help="Section key (use 'sections' command to list)"),
    headless: bool = typer.Option(False, "--headless", "-h", help="Run browser in headless mode"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save output to file"),
):
    """Fetch a theory section from Fluent Theory Guide."""

    if section not in THEORY_URLS:
        console.print(f"[red]Unknown section: {section}[/red]")
        console.print(f"Available sections: {', '.join(THEORY_URLS.keys())}")
        raise typer.Exit(1)

    with console.status(f"Fetching {section}..."):
        result = asyncio.run(fetch_section(section, headless=headless))

    if result:
        console.print(Panel(
            f"[bold]{result.title}[/bold]\n\n"
            f"[dim]URL: {result.url}[/dim]\n"
            f"[dim]Path: {' > '.join(result.breadcrumb)}[/dim]",
            title="Fetched Successfully"
        ))

        if output:
            with open(output, "w") as f:
                f.write(f"# {result.title}\n\n")
                f.write(f"URL: {result.url}\n")
                f.write(f"Path: {' > '.join(result.breadcrumb)}\n\n")
                f.write(result.content)
            console.print(f"[green]Saved to {output}[/green]")
        else:
            console.print("\n" + result.content[:5000])
            if len(result.content) > 5000:
                console.print(f"\n[dim]... ({len(result.content)} total chars, use -o to save full content)[/dim]")
    else:
        console.print("[red]Failed to fetch content[/red]")
        raise typer.Exit(1)


@app.command()
def url(
    doc_path: str = typer.Argument(..., help="URL path like 'corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html'"),
    headless: bool = typer.Option(False, "--headless", "-h", help="Run browser in headless mode"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save output to file"),
):
    """Fetch documentation by direct URL path.

    Example: fluent-doc url "corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html"
    """

    async def _fetch():
        async with FluentDocFetcher(headless=headless) as fetcher:
            return await fetcher.fetch_by_url(doc_path)

    with console.status(f"Fetching: {doc_path}"):
        result = asyncio.run(_fetch())

    if result:
        console.print(Panel(
            f"[bold]{result.title}[/bold]\n\n"
            f"[dim]URL: {result.url}[/dim]",
            title="Fetched Successfully"
        ))

        if output:
            with open(output, "w") as f:
                f.write(f"# {result.title}\n\n")
                f.write(f"URL: {result.url}\n\n")
                f.write(result.content)
            console.print(f"[green]Saved to {output}[/green]")
        else:
            console.print("\n" + result.content[:5000])
    else:
        console.print("[red]Failed to fetch content[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    headless: bool = typer.Option(False, "--headless", "-h", help="Run browser in headless mode"),
):
    """Search Fluent documentation (uses site search)."""

    async def _search():
        async with FluentDocFetcher(headless=headless) as fetcher:
            return await fetcher.search(query)

    with console.status(f"Searching: {query}"):
        result = asyncio.run(_search())

    if result:
        console.print(result[:8000])
    else:
        console.print("[red]Search failed[/red]")
        raise typer.Exit(1)


@app.command()
def find(
    query: str = typer.Argument(..., help="Search query (e.g., 'SST k-omega', 'natural convection')"),
    guide: str = typer.Option("theory", "--guide", "-g", help="Guide to search: theory, user, tui"),
    headless: bool = typer.Option(False, "--headless", "-h", help="Run browser in headless mode"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save output to file"),
    version: str = typer.Option("v252", "--version", "-v", help="Fluent version (e.g., v252, v251)"),
):
    """Find and fetch a section by searching the TOC dynamically.

    This is the recommended command as it doesn't rely on hardcoded URLs
    and works across different Fluent versions.

    Examples:
        fluent-doc find "SST k-omega"
        fluent-doc find "natural convection" -o convection.txt
        fluent-doc find "boundary conditions" --guide user
        fluent-doc find "heat transfer" --version v251
    """

    async def _find():
        async with FluentDocFetcher(headless=headless, version=version) as fetcher:
            return await fetcher.fetch_by_search(query, guide)

    with console.status(f"Finding '{query}' in {guide} guide..."):
        result = asyncio.run(_find())

    if result:
        console.print(Panel(
            f"[bold]{result.title}[/bold]\n\n"
            f"[dim]URL: {result.url}[/dim]",
            title="Found and Fetched"
        ))

        if output:
            with open(output, "w") as f:
                f.write(f"# {result.title}\n\n")
                f.write(f"URL: {result.url}\n\n")
                f.write(result.content)
            console.print(f"[green]Saved to {output}[/green]")
        else:
            console.print("\n" + result.content[:5000])
            if len(result.content) > 5000:
                console.print(f"\n[dim]... ({len(result.content)} total chars, use -o to save full content)[/dim]")
    else:
        console.print("[red]Section not found[/red]")
        raise typer.Exit(1)


@app.command()
def toc(
    guide: str = typer.Option("theory", "--guide", "-g", help="Guide: theory, user, tui"),
    headless: bool = typer.Option(False, "--headless", "-h", help="Run browser in headless mode"),
    version: str = typer.Option("v252", "--version", "-v", help="Fluent version"),
    filter: Optional[str] = typer.Option(None, "--filter", "-f", help="Filter entries by text"),
):
    """List all sections from a guide's Table of Contents.

    Examples:
        fluent-doc toc
        fluent-doc toc --guide user
        fluent-doc toc --filter turbulence
    """

    async def _toc():
        async with FluentDocFetcher(headless=headless, version=version) as fetcher:
            return await fetcher.build_toc_index(guide)

    with console.status(f"Building TOC index for {guide} guide..."):
        entries = asyncio.run(_toc())

    if not entries:
        console.print("[red]Failed to build TOC index[/red]")
        raise typer.Exit(1)

    # Filter if specified
    if filter:
        filter_lower = filter.lower()
        entries = [e for e in entries if filter_lower in e.title.lower()]

    table = Table(title=f"{guide.title()} Guide - Table of Contents ({len(entries)} entries)")
    table.add_column("Section", style="cyan", width=12)
    table.add_column("Title", style="green")

    for entry in entries[:100]:  # Limit to first 100 for display
        table.add_row(entry.section_number or "-", entry.title[:70])

    console.print(table)

    if len(entries) > 100:
        console.print(f"[dim]... and {len(entries) - 100} more entries (use --filter to narrow down)[/dim]")


def main():
    app()


if __name__ == "__main__":
    main()
