#!/usr/bin/env python3

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from scrap_core import fetch, extract, apply_filters, dedupe

console = Console()
err_console = Console(stderr=True)


def render(all_results, fmt, output):
    if fmt == "json":
        payload = json.dumps(all_results, indent=2, ensure_ascii=False)
        _write(payload, output)

    elif fmt == "txt":
        lines = []
        for url, results in all_results.items():
            for r in results:
                lines.append(f"{r['value']}\t{r['href']}" if r["href"] else r["value"])
        _write("\n".join(lines), output)

    elif fmt == "md":
        lines = []
        for url, results in all_results.items():
            lines.append(f"## {url}\n")
            for r in results:
                if r["href"]:
                    lines.append(f"- [{r['value'] or r['href']}]({r['href']})")
                else:
                    lines.append(f"- {r['value']}")
            lines.append("")
        _write("\n".join(lines), output)

    else:  # table, terminal only — ignores --output beyond a warning
        if output:
            err_console.print("[yellow]--format table can't be saved to a file, printing to terminal instead[/]")
        for url, results in all_results.items():
            table = Table(title=url, show_lines=False)
            table.add_column("#", style="dim", width=4)
            table.add_column("value", overflow="fold")
            has_href = any(r["href"] for r in results)
            if has_href:
                table.add_column("link", style="cyan", overflow="fold")
            for i, r in enumerate(results, 1):
                row = [str(i), r["value"] or "—"]
                if has_href:
                    row.append(r["href"] or "")
                table.add_row(*row)
            console.print(table)
            console.print(f"[dim]{len(results)} result(s)[/]\n")


def _write(content, output):
    if output:
        Path(output).write_text(content, encoding="utf-8")
        err_console.print(f"[green]saved to {output}[/]")
    else:
        console.print(content)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("urls", nargs=-1)
@click.option("--file", "url_file", type=click.Path(exists=True), help="File with one URL per line")
@click.option("--css", help="CSS selector to extract (e.g. 'h2.title::text')")
@click.option("--xpath", help="XPath expression to extract")
@click.option("--links", is_flag=True, help="Extract all links (text + resolved href)")
@click.option("--images", is_flag=True, help="Extract all image sources")
@click.option("--text", is_flag=True, help="Extract cleaned page text, line by line")
@click.option("--contains", help="Keep only results containing this keyword")
@click.option("--regex", help="Keep only results matching this regex")
@click.option("--exclude", help="Drop results containing this keyword")
@click.option("--stealth", is_flag=True, help="Force StealthyFetcher (anti-bot sites)")
@click.option("--timeout", default=30, show_default=True, help="Fetch timeout in seconds")
@click.option("--limit", type=int, default=0, help="Max results per URL (0 = no limit)")
@click.option("--no-dedupe", is_flag=True, help="Keep duplicate results")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "txt", "md"]), default="table")
@click.option("-o", "--output", type=click.Path(), help="Write to file instead of stdout")
def main(urls, url_file, css, xpath, links, images, text, contains, regex,
         exclude, stealth, timeout, limit, no_dedupe, fmt, output):
    """Fetch URL(s) with scrapling and print only what you asked for.

    Examples:

      scrap https://example.com --links --contains blog

      scrap https://example.com --css "h2.title::text" --format md -o titles.md

      scrap --file urls.txt --text --exclude cookie --limit 20
    """
    url_list = list(urls)
    if url_file:
        url_list += [l.strip() for l in Path(url_file).read_text().splitlines() if l.strip()]

    if not url_list:
        raise click.UsageError("Give at least one URL, or pass --file urls.txt")

    active_filters = sum(bool(x) for x in (css, xpath, links, images, text))
    if active_filters > 1:
        raise click.UsageError("Pick only one of --css / --xpath / --links / --images / --text")

    all_results = {}
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=err_console, transient=True) as progress:
        for url in url_list:
            task = progress.add_task(f"fetching {url}", total=None)
            try:
                resp, mode = fetch(url, stealth=stealth, timeout=timeout)
            except Exception as e:
                progress.remove_task(task)
                err_console.print(f"[red]FAILED[/] {url} — {e}")
                continue
            progress.remove_task(task)

            status_color = "green" if resp.status < 300 else "yellow" if resp.status < 400 else "red"
            err_console.print(f"[{status_color}]{resp.status}[/] {url} [dim]({mode})[/]")

            results = extract(resp, css=css, xpath=xpath, links=links, images=images, text=text)
            results = apply_filters(results, contains=contains, regex=regex, exclude=exclude)
            if not no_dedupe:
                results = dedupe(results)
            if limit:
                results = results[:limit]

            all_results[url] = results

    if not any(all_results.values()):
        err_console.print("[yellow]No results matched your filters.[/]")
        sys.exit(1)

    render(all_results, fmt, output)


if __name__ == "__main__":
    main()
