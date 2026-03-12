import click
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os


def serve_docs(host: str = "localhost", port: int = 8080):
    """Start local HTTP server to browse saved documentation."""
    docs_dir = Path.home() / ".doc-grab" / "docs"

    if not docs_dir.exists():
        click.echo(f"Error: No documentation found at {docs_dir}")
        click.echo("Run 'doc-greb fetch <url>' first to download docs.")
        return

    # Change to docs directory
    os.chdir(docs_dir)

    handler = SimpleHTTPRequestHandler
    server = HTTPServer((host, port), handler)

    click.echo(f"Serving documentation at http://{host}:{port}")
    click.echo(f"Directory: {docs_dir}")
    click.echo("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nServer stopped.")
        server.shutdown()


if __name__ == "__main__":
    import sys

    host = "localhost"
    port = 8080

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    serve_docs(host, port)
