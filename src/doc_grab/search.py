import click
import re
from pathlib import Path
from doc_grab.store import get_store_path


def search_docs(
    query: str, source: str = None, limit: int = 10, text_only: bool = False
):
    """Search through saved documentation.

    Args:
        query: Search term (regex)
        source: Filter by source name
        limit: Max results
        text_only: Search only .txt (clean) files
    """
    docs_dir = get_store_path() / "docs"

    if not docs_dir.exists():
        return []

    results = []
    pattern = re.compile(query, re.IGNORECASE)

    for source_dir in docs_dir.iterdir():
        if not source_dir.is_dir():
            continue

        if source and source_dir.name != source:
            continue

        # Search through files
        extensions = ["*.txt"] if text_only else ["*.html", "*.txt", "*.md"]

        for ext in extensions:
            for file in source_dir.glob(ext):
                if file.name == "metadata.json":
                    continue

                try:
                    content = file.read_text(encoding="utf-8")

                    for i, line in enumerate(content.split("\n"), 1):
                        if pattern.search(line):
                            results.append(
                                {
                                    "file": str(file.relative_to(docs_dir)),
                                    "line": i,
                                    "snippet": line.strip()[:200],
                                }
                            )
                            if len(results) >= limit:
                                return results

                except Exception:
                    continue

    return results


if __name__ == "__main__":
    click.echo("Use as CLI module")
