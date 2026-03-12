<div align="center">

<img src="https://raw.githubusercontent.com/Kandar-dev/docgrab/main/assets/logo.png" alt="DocGrab" width="200"/>

# DocGrab

### Fetch and manage documentation from any website

[![PyPI Version](https://img.shields.io/pypi/v/doc-grab.svg)](https://pypi.org/project/doc-grab/)
[![Python Version](https://img.shields.io/python/pyversion/doc-grab)](https://pypi.org/project/doc-grab/)
[![License](https://img.shields.io/pypi/l/doc-grab)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/alfa-rsa/docgrab)](https://github.com/alfa-rsa/docgrab/stargazers)

<p>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-2.0+-2D3748?style=flat&logo=playwright&logoColor=white)](https://playwright.dev/)
[![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4.12-333333?style=flat&logo=beautifulsoup&logoColor=white)](https://www.crummy.com/software/BeautifulSoup/)
[![httpx](https://img.shields.io/badge/httpx-0.27-005B96?style=flat)](https://www.python-httpx.org/)
[![Click](https://img.shields.io/badge/Click-8.1-000000?style=flat&logo=click&logoColor=white)](https://click.palletsprojects.com/)

</p>

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Commands](#commands) • [Examples](#examples) • [Tech Stack](#tech-stack) • [License](#license)

---

</div>

## Why DocGrab?

Many libraries have documentation websites but lack easy integration options. DocGrab solves this by downloading docs for offline use with multiple format options.

> **Built for:** Developers • Offline Reading • Local Search • CLI Tools

## Features

<div align="center">

| Feature | Description |
|---------|-------------|
| 🗺️ **Smart URL Discovery** | Finds docs even without sitemaps using wordlists and nav parsing |
| ⚡ **JavaScript Rendering** | Works with SPA/dynamic sites using Playwright |
| 🔍 **Framework Detection** | Auto-detects Docusaurus, GitBook, Swagger, Sphinx, MkDocs |
| 🌐 **Subdomain Discovery** | Checks docs., api., developer. subdomains automatically |
| 📄 **Multiple Formats** | HTML, Markdown, Plain text |
| 🔎 **Full-text Search** | Search across all saved docs instantly |
| 🎯 **Priority Sorting** | Fetches most important doc pages first |

</div>

## Installation

### From PyPI (Recommended)

```bash
pip install doc-grab
```

### From Source

```bash
git clone https://github.com/alfa-rsa/docgrab.git
cd docgrab
pip install -e .
```

### With JavaScript Support

```bash
pip install doc-grab[js]
playwright install chromium
```

## Quick Start

```bash
# Fetch a single page
doc-grab fetch https://docs.python.org

# Fetch with full power (sitemap + discover + subdomains + JS)
doc-grab fetch https://example.com --discover --sitemap --subdomains --js

# Search across all docs
doc-grab search "authentication"

# Serve locally
doc-grab serve
```

## Commands

| Command | Description |
|---------|-------------|
| `doc-grab fetch <url>` | Fetch documentation |
| `doc-grab list` | List saved docs |
| `doc-grab search <query>` | Search docs |
| `doc-grab refresh <name>` | Update docs |
| `doc-grab delete <name>` | Remove docs |
| `doc-grab serve` | Serve locally |

## Fetch Options

| Flag | Short | Description |
|------|-------|-------------|
| `--recursive` | `-r` | Follow all links |
| `--sitemap` | `-s` | Use sitemap.xml |
| `--discover` | `-d` | Wordlist + nav parsing |
| `--subdomains` | `-S` | Check docs., api. subdomains |
| `--priority` | `-p` | Prioritize doc URLs |
| `--js` | `-j` | JavaScript rendering |
| `--max-pages` | `-m` | Limit pages |
| `--name` | `-n` | Custom name |

## Examples

```bash
# Basic fetch
doc-grab fetch https://docs.python.org

# For JavaScript sites (React, Vue, etc)
doc-grab fetch https://react.dev --js

# For sites without sitemap (uses wordlist)
doc-grab fetch https://example.com --discover

# Full power - everything enabled
doc-grab fetch https://stripe.com --discover --sitemap --subdomains --priority --js

# Search across all docs
doc-grab search "authentication"

# Search specific doc
doc-grab search "function" --source python

# Update existing docs
doc-grab refresh python
```

## Output

Each fetch saves three formats:

```
docs/
└── my-docs/
    ├── index.html    # Original HTML
    ├── index.md      # Markdown
    └── index.txt     # Clean plain text
```

## Storage

Docs are saved to: `~/.doc-grab/docs/`

```
~/.doc-grab/
├── docs/
│   ├── flask/
│   │   ├── index.html
│   │   ├── index.md
│   │   └── metadata.json
│   └── python/
└── server.log
```

## Tech Stack

<div align="center">

### Built With

| Technology | Purpose |
|------------|---------|
| <img src="https://www.python.org/static/community_logos/python-logo-master-v3-TM.png" width="80"/> | Core language |
| <img src="https://click.palletsprojects.com/en/latest/_static/click-logo.png" width="80"/> | CLI framework |
| <img src="https://www.crummy.com/software/BeautifulSoup/bs4/static/logo-150.png" width="60"/> | HTML parsing |
| <img src="https://www.python-httpx.org/logo.svg" width="80"/> | HTTP client |
| <img src="https://playwright.dev/python/static/playwright-logo.svg" width="80"/> | JS rendering |
| <img src="https://urllib3.readthedocs.io/en/latest/_static/urllib3.png" width="60"/> | HTTP handling |

### Supported Frameworks

<p>

<img src="https://docusaurus.io/img/docusaurus.svg" width="40"/> 
<img src="https://swagger.io/wp-content/uploads/2020/02/swagger-logo-horizontal.png" width="60"/>
<img src="https://files.readthedocs.io/images/projects/logo-word.svg" width="80"/>
<img src="https://www.mkdocs.org/img/logo.svg" width="60"/>

</p>

Docusaurus • GitBook • Swagger/OpenAPI • Sphinx • MkDocs • ReadTheDocs

</div>

## Roadmap

- [ ] Support for more documentation frameworks
- [ ] Interactive CLI with autocomplete

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Star us on GitHub** ⭐ • **Report bugs** 🐛 • **Request features** 💡

Made with ❤️ by [Kandar](https://kandar.io)

</div>
