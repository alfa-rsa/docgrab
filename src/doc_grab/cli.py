import click
from pathlib import Path
from doc_grab.fetch import fetch_docs, fetch_with_playwright
from doc_grab.search import search_docs
from doc_grab.store import list_docs, delete_docs, init_store
from doc_grab.serve import serve_docs
from doc_grab.web_index import generate_index
from doc_grab.interactive import interactive_search


DOCS = {
    "python": ("https://docs.python.org/3/", 50),
    "python-lib": ("https://docs.python.org/3/library/", 50),
    "flask": ("https://flask.palletsprojects.com/", 30),
    "django": ("https://docs.djangoproject.com/en/stable/", 50),
    "fastapi": ("https://fastapi.tiangolo.com/", 30),
    "requests": ("https://requests.readthedocs.io/en/latest/", 30),
    "click": ("https://click.palletsprojects.com/", 20),
    "redis": ("https://redis.io/docs/", 30),
    "docker": ("https://docs.docker.com/", 30),
    "kubernetes": ("https://kubernetes.io/docs/", 30),
    "react": ("https://react.dev/", 30),
    "vue": ("https://vuejs.org/guide/", 30),
    "nextjs": ("https://nextjs.org/docs", 30),
    "typescript": ("https://www.typescriptlang.org/docs/", 30),
    "rust": ("https://doc.rust-lang.org/book/", 30),
    "go": ("https://go.dev/doc/", 30),
    "java": ("https://docs.oracle.com/en/java/javase/21/docs/api/", 30),
    "git": ("https://git-scm.com/doc", 20),
}


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """DocGrab - Fetch and manage documentation from any website."""
    pass


@cli.command()
@click.argument("name", required=False)
def add(name):
    """Add common documentation sources quickly."""
    if not name:
        click.echo("Available documentation sources:")
        click.echo("")
        for key in sorted(DOCS.keys()):
            url, pages = DOCS[key]
            click.echo(f"  {key:15} - {url}")
        click.echo("")
        click.echo("Usage: doc-greb add <name>")
        return

    if name not in DOCS:
        click.echo(f"Unknown: {name}")
        click.echo("Run 'doc-greb add' to see available sources.")
        return

    url, max_pages = DOCS[name]
    fetch_docs(url, recursive=True, max_pages=max_pages, name=name)
    generate_index()


@cli.command()
@click.argument("source")
@click.option(
    "--recursive", "-r", is_flag=True, help="Recursively fetch all linked pages"
)
@click.option(
    "--max-pages", "-m", default=50, help="Maximum pages to fetch in recursive mode"
)
@click.option(
    "--name", "-n", default=None, help="Custom name for this documentation source"
)
@click.option(
    "--js",
    "-j",
    "javascript",
    is_flag=True,
    help="Use Playwright for JavaScript-rendered content",
)
@click.option(
    "--sitemap",
    "-s",
    is_flag=True,
    help="Use sitemap.xml to discover URLs (faster, more complete)",
)
@click.option(
    "--priority",
    "-p",
    is_flag=True,
    help="Prioritize doc-like URLs (docs/, api/, guide/)",
)
@click.option(
    "--discover",
    "-d",
    is_flag=True,
    help="Use wordlist + nav parsing to discover docs (for sites without sitemap)",
)
@click.option(
    "--subdomains",
    "-S",
    is_flag=True,
    help="Also check subdomains (docs., api., developer.)",
)
def fetch(
    source,
    recursive,
    max_pages,
    name,
    javascript,
    sitemap,
    priority,
    discover,
    subdomains,
):
    """Fetch documentation from URL or local directory."""
    if source.startswith("http://") or source.startswith("https://"):
        if javascript:
            fetch_with_playwright(
                source,
                recursive=recursive,
                max_pages=max_pages,
                name=name,
                use_sitemap=sitemap,
                prioritize=priority,
                discover=discover,
                subdomains=subdomains,
            )
        else:
            fetch_docs(
                source,
                recursive=recursive,
                max_pages=max_pages,
                name=name,
                use_sitemap=sitemap,
                prioritize=priority,
                discover=discover,
                subdomains=subdomains,
            )
    else:
        path = Path(source)
        if path.is_dir():
            click.echo(f"Fetching from local directory: {path}")
        elif path.is_file():
            click.echo(f"Fetching from file: {path}")
        else:
            click.echo(f"Error: {source} is not a valid URL, directory, or file")


@cli.command()
@click.argument("query")
@click.option("--source", "-s", default=None, help="Search only in specific source")
@click.option("--limit", "-l", default=10, help="Maximum results to show")
@click.option("--text", "-t", is_flag=True, help="Search only .txt (clean) files")
def search(query, source, limit, text):
    """Search through saved documentation."""
    results = search_docs(query, source=source, limit=limit, text_only=text)

    if not results:
        click.echo("No results found.")
        return

    for i, result in enumerate(results, 1):
        click.echo(f"\n--- Result {i} ---")
        click.echo(f"File: {result['file']}")
        click.echo(f"Line: {result['line']}")
        click.echo(result["snippet"])


@cli.command()
@click.argument("query")
@click.option("--source", "-s", default=None, help="Search only in specific source")
@click.option("--limit", "-l", default=20, help="Maximum results")
@click.option("--text", "-t", is_flag=True, help="Search only .txt files")
def isearch(query, source, limit, text):
    """Interactive search with preview and selection."""
    result = interactive_search(query, source=source, limit=limit, text_only=text)

    if result:
        click.echo("\n\033[1;32mSelected:\033[0m")
        click.echo(f"File: {result['file']}")
        click.echo(f"Line: {result['line']}")
        click.echo(result["snippet"])


@cli.command()
@click.option("--host", "-h", default="localhost", help="Host to bind to")
@click.option("--port", "-p", default=8080, help="Port to listen on")
@click.option("--bg", "-b", is_flag=True, help="Run in background")
def serve(host, port, bg):
    """Start local server to browse saved documentation."""
    if bg:
        import subprocess
        import sys
        import os

        log_file = Path.home() / ".doc-grab" / "server.log"

        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "doc_grab",
                "serve",
                "--host",
                host,
                "--port",
                str(port),
            ],
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
            cwd=str(Path.home() / ".doc-grab" / "docs"),
        )
        click.echo(f"Server started in background on http://{host}:{port}")
        click.echo(f"Log: {log_file}")
    else:
        serve_docs(host, port)


@cli.command()
@click.argument("source")
@click.option("--max-pages", "-m", default=50, help="Maximum pages to fetch")
def refresh(source, max_pages):
    """Refresh/update existing documentation."""
    from doc_grab.store import list_docs

    docs = list_docs(source)
    if not docs:
        click.echo(f"No documentation found for '{source}'")
        return

    doc = docs[0]
    url = doc.get("url")
    if not url:
        click.echo(f"No URL found for '{source}'. Try deleting and re-adding.")
        return

    # Delete and re-fetch
    from doc_grab.store import delete_docs

    delete_docs(source)

    fetch_docs(url, recursive=True, max_pages=max_pages, name=source)
    generate_index()
    click.echo(f"Refreshed: {source}")


@cli.command()
@click.argument("source", required=False)
def list(source):
    """List saved documentation sources."""
    docs = list_docs(source)

    if not docs:
        click.echo("No documentation saved yet.")
        return

    for doc in docs:
        click.echo(f"{doc['name']}: {doc['url']} ({doc['pages']} pages)")


@cli.command()
@click.argument("source")
def delete(source):
    """Delete saved documentation by source name."""
    delete_docs(source)


@cli.command()
def init():
    """Initialize DocGrab storage."""
    init_store()


if __name__ == "__main__":
    cli()
