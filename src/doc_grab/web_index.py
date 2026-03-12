import click
import json
from pathlib import Path


def get_store_path() -> Path:
    store = Path.home() / ".doc-grab"
    store.mkdir(parents=True, exist_ok=True)
    return store


def generate_index():
    """Generate index.html for the documentation server."""
    docs_dir = get_store_path() / "docs"

    if not docs_dir.exists():
        return None

    docs = []
    for source_dir in docs_dir.iterdir():
        if not source_dir.is_dir():
            continue

        metadata_file = source_dir / "metadata.json"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            docs.append(
                {
                    "name": source_dir.name,
                    "url": metadata.get("url", ""),
                    "pages": metadata.get("pages", 0),
                    "fetched_at": metadata.get("fetched_at", ""),
                }
            )
        else:
            pages = len(list(source_dir.glob("*.html")))
            docs.append(
                {"name": source_dir.name, "url": "", "pages": pages, "fetched_at": ""}
            )

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocGrab - Documentation Library</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .docs {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }
        .doc-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .doc-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .doc-card h3 { margin-bottom: 8px; }
        .doc-card h3 a {
            color: #2563eb;
            text-decoration: none;
        }
        .doc-card h3 a:hover { text-decoration: underline; }
        .doc-meta { color: #666; font-size: 14px; }
        .doc-url { 
            color: #666; 
            font-size: 12px; 
            overflow: hidden; 
            text-overflow: ellipsis; 
            white-space: nowrap;
            margin-top: 8px;
        }
        .search-box {
            margin-bottom: 30px;
        }
        .search-box input {
            width: 100%;
            padding: 12px 16px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .no-docs {
            text-align: center;
            color: #666;
            padding: 40px;
        }
    </style>
</head>
<body>
    <h1>📚 DocGrab</h1>
    <p class="subtitle">Your local documentation library</p>
    
    <div class="search-box">
        <input type="text" id="search" placeholder="Search documentation... (Ctrl+K)" autofocus>
    </div>
    
    <div class="docs" id="docs">
"""

    if not docs:
        html += '<div class="no-docs">No documentation saved yet.<br><br>Run: doc-greb fetch https://docs.example.com/</div>'
    else:
        for doc in docs:
            name = doc["name"].replace("_", " ").replace("-", " ")
            html += f"""
        <div class="doc-card">
            <h3><a href="{doc["name"]}/">{name}</a></h3>
            <div class="doc-meta">{doc["pages"]} pages</div>
            <div class="doc-url" title="{doc["url"]}">{doc["url"]}</div>
        </div>
"""

    html += """
    </div>
    
    <script>
        document.getElementById('search').addEventListener('keyup', function(e) {
            var query = this.value.toLowerCase();
            var cards = document.querySelectorAll('.doc-card');
            cards.forEach(function(card) {
                var text = card.textContent.toLowerCase();
                card.style.display = text.includes(query) ? 'block' : 'none';
            });
        });
        
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('search').focus();
            }
        });
    </script>
</body>
</html>"""

    index_file = docs_dir / "index.html"
    index_file.write_text(html)
    return index_file
