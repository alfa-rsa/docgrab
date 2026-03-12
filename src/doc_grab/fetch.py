import click
import httpx
import urllib3
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from doc_grab.store import get_store_path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def discover_urls_from_sitemap(base_url: str, max_urls: int = 200) -> list:
    """Discover all URLs from sitemap.xml and sitemap indexes.

    Handles:
    - Standard sitemap.xml
    - Sitemap indexes (sitemap-index.xml)
    - Nested sitemaps
    """
    discovered = []
    parsed = urlparse(base_url)
    base_domain = parsed.netloc

    common_sitemap_paths = [
        "/sitemap.xml",
        "/sitemap-index.xml",
        "/sitemapindex.xml",
        "/sitemaps.xml",
    ]

    client = httpx.Client(timeout=15.0, verify=False, follow_redirects=True)

    def fetch_sitemap(url: str, depth: int = 0):
        if depth > 3 or len(discovered) >= max_urls:
            return

        try:
            response = client.get(url)
            if response.status_code != 200:
                return

            content = response.text

            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                return

            root_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

            if root_tag == "sitemapindex":
                for sitemap in root:
                    sitemap_tag = (
                        sitemap.tag.split("}")[-1]
                        if "}" in sitemap.tag
                        else sitemap.tag
                    )
                    if sitemap_tag == "sitemap":
                        loc = None
                        for child in sitemap:
                            child_tag = (
                                child.tag.split("}")[-1]
                                if "}" in child.tag
                                else child.tag
                            )
                            if child_tag == "loc":
                                loc = child.text
                                break
                        if loc:
                            fetch_sitemap(loc, depth + 1)
            elif root_tag == "urlset":
                for url_elem in root:
                    url_tag = (
                        url_elem.tag.split("}")[-1]
                        if "}" in url_elem.tag
                        else url_elem.tag
                    )
                    if url_tag == "url":
                        loc = None
                        for child in url_elem:
                            child_tag = (
                                child.tag.split("}")[-1]
                                if "}" in child.tag
                                else child.tag
                            )
                            if child_tag == "loc":
                                loc = child.text
                                break
                        if loc:
                            parsed_url = urlparse(loc)
                            if parsed_url.netloc == base_domain:
                                if loc not in discovered:
                                    discovered.append(loc)

        except Exception as e:
            pass

    for sitemap_path in common_sitemap_paths:
        sitemap_url = f"{parsed.scheme}://{base_domain}{sitemap_path}"
        fetch_sitemap(sitemap_url)
        if discovered:
            break

    client.close()
    return discovered[:max_urls]


def prioritize_doc_urls(urls: list, base_url: str) -> list:
    """Sort URLs by likelihood of being documentation pages.

    Priority order:
    1. /docs/, /guide/, /tutorial/, /api/
    2. /v*/ (versioned docs)
    3. /reference/, /manual/
    4. Index/pages
    5. Other pages
    """
    priority_scores = {
        "docs": 100,
        "guide": 95,
        "tutorial": 90,
        "api": 85,
        "reference": 80,
        "manual": 75,
        "v1": 70,
        "v2": 70,
        "v3": 70,
        "latest": 65,
        "stable": 65,
        "index": 50,
    }

    def score_url(url: str) -> int:
        url_lower = url.lower()
        score = 0
        for keyword, pts in priority_scores.items():
            if keyword in url_lower:
                score = max(score, pts)
                break
        return score

    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    scored = []
    for url in urls:
        if url.startswith(base):
            score = score_url(url)
            scored.append((score, url))

    scored.sort(key=lambda x: -x[0])
    return [url for _, url in scored]


def is_same_domain_or_subdomain(url1: str, url2: str) -> bool:
    """Check if url2 is same domain or subdomain of url1."""
    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)

    domain1 = parsed1.netloc.lower()
    domain2 = parsed2.netloc.lower()

    if domain1 == domain2:
        return True

    if domain2.endswith(f".{domain1}") or domain1.endswith(f".{domain2}"):
        return True

    return False


COMMON_SUBDOMAINS = [
    "docs",
    "documentation",
    "developer",
    "developers",
    "api",
    "reference",
    "learn",
    "guide",
    "help",
    "support",
    "wiki",
    "manual",
    "blog",
    "community",
]


def discover_subdomains(base_url: str, max_subdomains: int = 10) -> list:
    """Discover common documentation subdomains.

    Tries common subdomain prefixes like docs., api., developer., etc.
    """
    discovered = []
    parsed = urlparse(base_url)
    base_domain = parsed.netloc

    if not base_domain:
        return discovered

    if ":" in base_domain:
        base_domain = base_domain.split(":")[0]

    client = httpx.Client(timeout=8.0, verify=False, follow_redirects=True)

    for subdomain in COMMON_SUBDOMAINS:
        if len(discovered) >= max_subdomains:
            break

        subdomain_url = f"{parsed.scheme}://{subdomain}.{base_domain}/"

        try:
            response = client.head(subdomain_url, follow_redirects=True)
            if response.status_code == 200:
                discovered.append(subdomain_url)
        except Exception:
            pass

    client.close()
    return discovered


DOC_PATH_WORDLIST = [
    "/docs",
    "/documentation",
    "/api",
    "/reference",
    "/guide",
    "/tutorial",
    "/tutorials",
    "/learn",
    "/manual",
    "/wiki",
    "/help",
    "/support",
    "/getting-started",
    "/quickstart",
    "/intro",
    "/introduction",
    "/basics",
    "/fundamentals",
    "/advanced",
    "/examples",
    "/sample",
    "/v1/docs",
    "/v2/docs",
    "/latest",
    "/stable",
    "/current",
    "/en/latest",
    "/en/v1",
    "/zh/latest",
    "/pt/latest",
    "/ja/latest",
]

DOC_KEYWORD_WORDLIST = [
    "documentation",
    "api reference",
    "getting started",
    "quick start",
    "tutorial",
    "guide",
    "manual",
    "examples",
    "learn",
    "docs",
    "reference",
]

FRAMEWORK_PATTERNS = {
    "docusaurus": [
        "/docs/{version}/",
        "/docs/next/",
        "/versioned_docs/",
        "docusaurus",
    ],
    "gitbook": [
        "/SUMMARY",
        "/docs/",
        "gitbook",
    ],
    "sphinx": [
        "/contents.rst",
        "/_build/",
        "/genindex",
        "sphinx",
    ],
    "swagger": [
        "/swagger",
        "/swagger-ui",
        "/api-docs",
        "/openapi.json",
        "/swagger.json",
    ],
    "redoc": [
        "/redoc",
        "/reference",
    ],
    "mkdocs": [
        "/mkdocs",
        "mkdocs",
    ],
    "readthedocs": [
        "/en/latest/",
        "/_build/html/",
        "readthedocs",
    ],
}


def detect_framework(html: str, url: str) -> str | None:
    """Detect the documentation framework used by examining HTML content."""
    html_lower = html.lower()
    url_lower = url.lower()

    for framework, patterns in FRAMEWORK_PATTERNS.items():
        for pattern in patterns:
            if pattern in html_lower or pattern in url_lower:
                return framework
    return None


def get_framework_urls(framework: str, base_url: str) -> list:
    """Get URLs specific to a detected framework."""
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    urls = []

    framework_url_map = {
        "docusaurus": [
            f"{base}/docs",
            f"{base}/docs/next",
            f"{base}/docs/{parsed.netloc.split('.')[0]}",
        ],
        "gitbook": [
            f"{base}/docs",
            f"{base}/SUMMARY",
        ],
        "swagger": [
            f"{base}/swagger",
            f"{base}/api-docs",
            f"{base}/swagger.json",
            f"{base}/openapi.json",
        ],
        "redoc": [
            f"{base}/redoc",
            f"{base}/openapi.json",
        ],
        "readthedocs": [
            f"{base}/en/latest",
            f"{base}/en/stable",
        ],
    }

    return framework_url_map.get(framework, [])


def discover_urls_common_paths(base_url: str, max_urls: int = 50) -> list:
    """Try common doc paths to discover documentation URLs.

    This is useful for sites without sitemaps.
    """
    discovered = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    client = httpx.Client(timeout=10.0, verify=False, follow_redirects=True)

    for path in DOC_PATH_WORDLIST:
        if len(discovered) >= max_urls:
            break

        url = f"{base}{path}/" if not path.endswith("/") else base + path
        if not url.endswith("/"):
            url += "/"

        try:
            response = client.head(url, follow_redirects=True)
            if response.status_code == 200:
                discovered.append(url)
        except Exception:
            pass

        url_without_slash = base + path
        try:
            response = client.head(url_without_slash, follow_redirects=True)
            if response.status_code == 200 and url_without_slash not in discovered:
                discovered.append(url_without_slash)
        except Exception:
            pass

    client.close()
    return discovered[:max_urls]


def discover_urls_from_nav(html: str, base_url: str) -> list:
    """Extract documentation links from navigation elements.

    Parses:
    - <nav> elements
    - Sidebar elements (aside, .sidebar, .nav)
    - Menu structures
    """
    soup = BeautifulSoup(html, "html.parser")
    doc_links = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    nav_selectors = [
        "nav",
        "aside",
        ".sidebar",
        ".nav",
        ".navigation",
        ".menu",
        "[role='navigation']",
        "[class*='sidebar']",
        "[class*='nav-menu']",
        "[id*='sidebar']",
        "[id*='navigation']",
    ]

    for selector in nav_selectors:
        for nav in soup.select(selector):
            for link in nav.find_all("a", href=True):
                href = link.get("href", "")

                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue

                if not href.startswith("http"):
                    href = urljoin(base_url, href)

                parsed_href = urlparse(href)
                if parsed_href.netloc == parsed.netloc:
                    if href not in doc_links:
                        doc_links.append(href)

    return doc_links


def get_doc_urls(
    base_url: str,
    use_sitemap: bool = False,
    prioritize: bool = False,
    max_urls: int = 50,
) -> list:
    """Main function to discover documentation URLs using all strategies.

    Strategy order:
    1. Try sitemap.xml (if use_sitemap=True)
    2. Try common doc paths
    3. Parse navigation for links
    4. Detect framework and get framework-specific URLs

    Returns list of URLs to fetch.
    """
    all_urls = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    if use_sitemap:
        sitemap_urls = discover_urls_from_sitemap(base_url, max_urls=max_urls * 2)
        if sitemap_urls:
            all_urls.extend(sitemap_urls)

    if len(all_urls) < max_urls:
        common_paths = discover_urls_common_paths(base_url, max_urls=max_urls)
        for url in common_paths:
            if url not in all_urls:
                all_urls.append(url)

    try:
        client = httpx.Client(timeout=15.0, verify=False, follow_redirects=True)
        response = client.get(base_url)
        if response.status_code == 200:
            framework = detect_framework(response.text, base_url)
            if framework:
                framework_urls = get_framework_urls(framework, base_url)
                for url in framework_urls:
                    if url not in all_urls:
                        all_urls.append(url)

            nav_links = discover_urls_from_nav(response.text, base_url)
            for url in nav_links:
                if url not in all_urls:
                    all_urls.append(url)
        client.close()
    except Exception:
        pass

    if prioritize and all_urls:
        all_urls = prioritize_doc_urls(all_urls, base_url)

    return all_urls[:max_urls]


def extract_clean_text(html: str, url: str) -> str:
    """Extract clean, readable text from HTML for offline consumption."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
            "iframe",
            "noscript",
            "svg",
            "meta",
            "link",
            "button",
            "input",
        ]
    ):
        tag.decompose()

    # Get title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    else:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    # Get main content - try common doc patterns
    content = None

    for selector in [
        "main",
        "article",
        ".content",
        "#content",
        ".doc-content",
        ".docs-content",
        ".bd-content",
        ".section",
    ]:
        content = soup.select_one(selector)
        if content:
            break

    if not content:
        content = soup.body or soup

    # Extract text
    text = content.get_text(separator="\n", strip=True)

    # Clean up
    import re

    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    text = "\n".join(lines)

    return f"# {title}\n\nSource: {url}\n\n---\n\n{text}"


def extract_markdown(html: str, url: str) -> str:
    """Extract Markdown from HTML, preserving code blocks and headers."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
            "iframe",
            "noscript",
            "svg",
            "meta",
            "link",
            "button",
            "input",
        ]
    ):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    else:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    md_lines = [f"# {title}", "", f"Source: {url}", "", "---", ""]

    content = None
    for selector in [
        "main",
        "article",
        ".content",
        "#content",
        ".doc-content",
        ".docs-content",
        ".bd-content",
        ".section",
    ]:
        content = soup.select_one(selector)
        if content:
            break
    if not content:
        content = soup.body or soup

    def process_element(element):
        result = []
        for child in element.children:
            if child.name is None:
                text = str(child).strip()
                if text:
                    result.append(text)
                continue

            tag_name = child.name

            if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                text = child.get_text(strip=True)
                level = int(tag_name[1])
                result.append(f"{'#' * level} {text}")
            elif tag_name == "p":
                text = child.get_text(strip=True)
                if text:
                    result.append(text)
            elif tag_name == "pre":
                code = child.get_text("\n", strip=True)
                if code:
                    lang = ""
                    if child.find("code"):
                        code_class = child.find("code").get("class", [])
                        for c in code_class:
                            if c.startswith("language-"):
                                lang = c.replace("language-", "")
                                break
                    result.append(f"```{lang}\n{code}\n```")
            elif tag_name == "code":
                text = child.get_text(strip=True)
                if "\n" in text:
                    result.append(f"```\n{text}\n```")
                else:
                    result.append(f"`{text}`")
            elif tag_name == "ul":
                for li in child.find_all("li", recursive=False):
                    text = li.get_text(strip=True)
                    result.append(f"- {text}")
            elif tag_name == "ol":
                for i, li in enumerate(child.find_all("li", recursive=False), 1):
                    text = li.get_text(strip=True)
                    result.append(f"{i}. {text}")
            elif tag_name == "a":
                href = child.get("href", "")
                text = child.get_text(strip=True)
                if text and href:
                    result.append(f"[{text}]({href})")
                elif text:
                    result.append(text)
            elif tag_name == "table":
                rows = child.find_all("tr")
                for tr in rows:
                    cells = tr.find_all(["th", "td"])
                    row_text = " | ".join(cell.get_text(strip=True) for cell in cells)
                    result.append(f"| {row_text} |")
            elif tag_name == "blockquote":
                text = child.get_text(strip=True)
                for line in text.split("\n"):
                    result.append(f"> {line}")
            else:
                result.extend(process_element(child))

        return result

    md_lines.extend(process_element(content))

    import re

    md_text = "\n".join(md_lines)
    md_text = re.sub(r"\n{3,}", "\n\n", md_text)

    return md_text


def fetch_with_playwright(
    url: str,
    recursive: bool = False,
    max_pages: int = 50,
    name: str = None,
    use_sitemap: bool = False,
    prioritize: bool = False,
    discover: bool = False,
    subdomains: bool = False,
):
    """Fetch documentation using Playwright for JavaScript-rendered content."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        click.echo(
            "Error: Playwright is not installed. Run: pip install playwright && playwright install chromium"
        )
        return

    click.echo(f"Fetching (JS mode): {url}")

    if not name:
        parsed = urlparse(url)
        name = parsed.netloc.replace(".", "_")

    docs_dir = get_store_path() / "docs" / name
    docs_dir.mkdir(parents=True, exist_ok=True)

    visited = set()
    to_visit = [url]
    pages_fetched = 0

    subdomain_urls = []
    if subdomains:
        click.echo("  Discovering subdomains...")
        subdomain_urls = discover_subdomains(url, max_subdomains=15)
        if subdomain_urls:
            click.echo(f"  Found {len(subdomain_urls)} subdomains")
            for sub_url in subdomain_urls:
                if sub_url not in to_visit:
                    to_visit.append(sub_url)

    if discover:
        click.echo("  Discovering URLs using wordlist + nav parsing...")
        discovered = get_doc_urls(
            url, use_sitemap=True, prioritize=prioritize, max_urls=max_pages
        )
        if discovered:
            click.echo(f"  Found {len(discovered)} URLs via discovery")
            to_visit = discovered[:max_pages]
            for sub_url in subdomain_urls:
                if sub_url not in to_visit:
                    to_visit.append(sub_url)
        else:
            click.echo("  No URLs discovered, using link crawling")
            to_visit = [url]
    elif use_sitemap:
        click.echo("  Discovering URLs from sitemap.xml...")
        sitemap_urls = discover_urls_from_sitemap(url, max_urls=max_pages * 2)
        if sitemap_urls:
            click.echo(f"  Found {len(sitemap_urls)} URLs from sitemap")
            if prioritize:
                sitemap_urls = prioritize_doc_urls(sitemap_urls, url)
                click.echo("  Prioritized doc-like URLs")
            to_visit = sitemap_urls[:max_pages]
        else:
            click.echo("  No sitemap found, using link crawling")
            to_visit = [url]
    elif recursive:
        to_visit = [url]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while to_visit and pages_fetched < max_pages:
            current_url = to_visit.pop(0)

            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                click.echo(f"  Fetching: {current_url}")
                page.goto(current_url, wait_until="networkidle", timeout=30000)
                html_content = page.content()

                parsed = urlparse(current_url)
                path = parsed.path.strip("/")

                if not path:
                    filename = "index.html"
                else:
                    filename = path.replace("/", "_")
                    if not filename.endswith(".html"):
                        filename += ".html"

                filepath = docs_dir / filename
                filepath.write_text(html_content, encoding="utf-8")

                text_content = extract_clean_text(html_content, current_url)
                text_filename = filename.replace(".html", ".txt")
                text_filepath = docs_dir / text_filename
                text_filepath.write_text(text_content, encoding="utf-8")

                md_content = extract_markdown(html_content, current_url)
                md_filename = filename.replace(".html", ".md")
                md_filepath = docs_dir / md_filename
                md_filepath.write_text(md_content, encoding="utf-8")

                pages_fetched += 1

                if recursive:
                    links = page.eval_on_selector_all(
                        "a[href]", "els => els.map(e => e.href)"
                    )
                    base_domain = urlparse(url).netloc

                    for href in links:
                        if not href:
                            continue

                        if href.startswith("#") or href.startswith("javascript:"):
                            continue

                        absolute_url = urljoin(current_url, href)
                        parsed_abs = urlparse(absolute_url)

                        if parsed_abs.netloc != base_domain:
                            continue

                        path_lower = parsed_abs.path.lower()
                        if any(
                            x in path_lower
                            for x in [
                                ".png",
                                ".jpg",
                                ".jpeg",
                                ".gif",
                                ".svg",
                                ".ico",
                                ".css",
                                ".js",
                                ".woff",
                                ".ttf",
                            ]
                        ):
                            continue

                        if absolute_url not in visited:
                            to_visit.append(absolute_url)

            except Exception as e:
                click.echo(f"  Error fetching {current_url}: {e}")

        browser.close()

    metadata = {
        "name": name,
        "url": url,
        "fetched_at": datetime.now().isoformat(),
        "pages": pages_fetched,
        "javascript": True,
    }

    metadata_file = docs_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))

    from doc_grab.web_index import generate_index

    generate_index()

    click.echo(f"Done! Fetched {pages_fetched} pages to {docs_dir}")


def fetch_docs(
    url: str,
    recursive: bool = False,
    max_pages: int = 50,
    name: str = None,
    use_sitemap: bool = False,
    prioritize: bool = False,
    discover: bool = False,
    subdomains: bool = False,
):
    """Fetch documentation from a URL."""
    click.echo(f"Fetching: {url}")

    if not name:
        parsed = urlparse(url)
        name = parsed.netloc.replace(".", "_")

    docs_dir = get_store_path() / "docs" / name
    docs_dir.mkdir(parents=True, exist_ok=True)

    visited = set()
    to_visit = [url]
    pages_fetched = 0

    subdomain_urls = []
    if subdomains:
        click.echo("  Discovering subdomains...")
        subdomain_urls = discover_subdomains(url, max_subdomains=15)
        if subdomain_urls:
            click.echo(f"  Found {len(subdomain_urls)} subdomains")
            for sub_url in subdomain_urls:
                if sub_url not in to_visit:
                    to_visit.append(sub_url)

    if discover:
        click.echo("  Discovering URLs using wordlist + nav parsing...")
        discovered = get_doc_urls(
            url, use_sitemap=True, prioritize=prioritize, max_urls=max_pages
        )
        if discovered:
            click.echo(f"  Found {len(discovered)} URLs via discovery")
            to_visit = discovered[:max_pages]
            for sub_url in subdomain_urls:
                if sub_url not in to_visit:
                    to_visit.append(sub_url)
        else:
            click.echo("  No URLs discovered, using link crawling")
    elif use_sitemap:
        click.echo("  Discovering URLs from sitemap.xml...")
        sitemap_urls = discover_urls_from_sitemap(url, max_urls=max_pages * 2)
        if sitemap_urls:
            click.echo(f"  Found {len(sitemap_urls)} URLs from sitemap")
            if prioritize:
                sitemap_urls = prioritize_doc_urls(sitemap_urls, url)
                click.echo("  Prioritized doc-like URLs")
            to_visit = sitemap_urls[:max_pages]
        else:
            click.echo("  No sitemap found, using link crawling")
            to_visit = [url]
    elif recursive:
        to_visit = [url]

    client = httpx.Client(timeout=30.0, verify=False, follow_redirects=True)

    while to_visit and pages_fetched < max_pages:
        current_url = to_visit.pop(0)

        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            click.echo(f"  Fetching: {current_url}")
            response = client.get(current_url)
            response.raise_for_status()

            # Save the page
            parsed = urlparse(current_url)
            path = parsed.path.strip("/")

            if not path:
                filename = "index.html"
            else:
                filename = path.replace("/", "_")
                if not filename.endswith(".html"):
                    filename += ".html"

            filepath = docs_dir / filename
            filepath.write_text(response.text, encoding="utf-8")

            # Save clean text version for offline reading
            text_content = extract_clean_text(response.text, current_url)
            text_filename = filename.replace(".html", ".txt")
            text_filepath = docs_dir / text_filename
            text_filepath.write_text(text_content, encoding="utf-8")

            # Save Markdown version
            md_content = extract_markdown(response.text, current_url)
            md_filename = filename.replace(".html", ".md")
            md_filepath = docs_dir / md_filename
            md_filepath.write_text(md_content, encoding="utf-8")

            pages_fetched += 1

            # Extract links for recursive fetch
            if recursive:
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = link["href"]

                    # Skip anchors and non-http links
                    if href.startswith("#") or href.startswith("javascript:"):
                        continue

                    absolute_url = urljoin(current_url, href)
                    parsed_abs = urlparse(absolute_url)

                    # Only follow links on same domain
                    if parsed_abs.netloc != urlparse(url).netloc:
                        continue

                    # Skip common non-doc links
                    path = parsed_abs.path.lower()
                    if any(
                        x in path
                        for x in [
                            ".png",
                            ".jpg",
                            ".jpeg",
                            ".gif",
                            ".svg",
                            ".ico",
                            ".css",
                            ".js",
                            ".woff",
                            ".ttf",
                        ]
                    ):
                        continue

                    if absolute_url not in visited:
                        to_visit.append(absolute_url)

        except Exception as e:
            click.echo(f"  Error fetching {current_url}: {e}")

    client.close()

    # Save metadata
    metadata = {
        "name": name,
        "url": url,
        "fetched_at": datetime.now().isoformat(),
        "pages": pages_fetched,
    }

    metadata_file = docs_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))

    # Generate index
    from doc_grab.web_index import generate_index

    generate_index()

    click.echo(f"Done! Fetched {pages_fetched} pages to {docs_dir}")


if __name__ == "__main__":
    click.echo("Use as CLI module")
