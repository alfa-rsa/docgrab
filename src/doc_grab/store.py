import click
from pathlib import Path
import json


def get_store_path() -> Path:
    """Get the storage directory path."""
    store_path = Path.home() / ".doc-grab"
    store_path.mkdir(parents=True, exist_ok=True)
    return store_path


def init_store():
    """Initialize the storage directory."""
    store_path = get_store_path()
    docs_dir = store_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"Initialized DocGrab storage at: {store_path}")


def list_docs(source: str = None):
    """List saved documentation sources."""
    docs_dir = get_store_path() / "docs"

    if not docs_dir.exists():
        return []

    results = []

    for source_dir in docs_dir.iterdir():
        if not source_dir.is_dir():
            continue

        if source and source_dir.name != source:
            continue

        metadata_file = source_dir / "metadata.json"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            results.append(metadata)
        else:
            # Count files
            pages = len(list(source_dir.glob("*.html")))
            results.append({"name": source_dir.name, "url": "unknown", "pages": pages})

    return results


def delete_docs(source: str):
    """Delete saved documentation by source name."""
    docs_dir = get_store_path() / "docs"
    source_dir = docs_dir / source

    if not source_dir.exists():
        click.echo(f"Error: No documentation found for '{source}'")
        return

    import shutil

    shutil.rmtree(source_dir)
    click.echo(f"Deleted documentation: {source}")


if __name__ == "__main__":
    click.echo("Use as CLI module")
