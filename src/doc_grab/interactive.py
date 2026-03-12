import click
from pathlib import Path


def interactive_search(query, source=None, limit=20, text_only=False):
    """Interactive search with numbered selection."""
    from doc_grab.search import search_docs

    click.echo(f"Searching for: {query}")

    # Search
    results = search_docs(query, source=source, limit=limit, text_only=text_only)

    if not results:
        click.echo("No results found.")
        return None

    # Show numbered results with preview
    click.echo(f"\n\033[1mFound {len(results)} results:\033[0m\n")

    # Show first 10 results with context
    display_results = results[:10]

    for i, result in enumerate(display_results):
        filename = result["file"].split("/")[-1]
        click.echo(
            f"\033[1;32m[{i + 1}]\033[0m \033[1m{filename}\033[0m line {result['line']}"
        )
        click.echo(f"    {result['snippet'][:80]}...")

    click.echo(
        f"\n\033[1mSelect result (1-{len(display_results)}) or 'p' for preview, 'q' to quit:\033[0m ",
        nl=False,
    )

    choice = input().strip().lower()

    if choice == "q":
        return None

    if choice == "p":
        # Show previews one by one
        idx = 0
        while True:
            if idx >= len(display_results):
                idx = 0

            result = display_results[idx]
            full_path = Path.home() / ".doc-grab" / "docs" / result["file"]

            # Get context around match
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                line_num = result["line"]
                start = max(0, line_num - 10)
                end = min(len(lines), line_num + 10)

                click.echo(
                    f"\n\033[1;36m--- {result['file']} (line {line_num}) ---\033[0m"
                )
                for i, line in enumerate(lines[start:end], start + 1):
                    prefix = "\033[1;31m→\033[0m" if i == line_num else "  "
                    click.echo(f"{prefix}\033[90m{i:4}\033[0m {line.rstrip()[:100]}")

            except Exception as e:
                click.echo(f"Error: {e}")

            click.echo(
                f"\n\033[1m[{idx + 1}/{len(display_results)}]\033[0m ← → navigate | Enter select | q quit: ",
                nl=False,
            )
            nav = input().strip().lower()

            if nav == "q":
                return None
            elif nav == "":
                return result
            elif nav == "j" or nav == "down" or nav == "→":
                idx += 1
            elif nav == "k" or nav == "up" or nav == "←":
                idx = max(0, idx - 1)

    # Number selection
    try:
        num = int(choice)
        if 1 <= num <= len(display_results):
            return display_results[num - 1]
    except ValueError:
        pass

    return None
