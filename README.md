# Galaxy Stats

Documentation site for "Once Upon a Galaxy Tournament Stats"

## Structure

- **`etl/`**: Python scripts that parse event HTML into JSON data
- **`frontend/`**: Astro + Starlight documentation site that displays the stats
- **`Makefile`**: Root-level build automation for all commands

## Quick Start

```bash
# Install all dependencies (Python + Node)
make install

# Process event data
make parse-event HTML=etl/context/2026-02.html EVENT_ID=2026-02

# Start frontend dev server
make dev

# Build for production
make build
```

## Workflow

1. **Process data** (ETL):
   ```bash
   make parse-event HTML=etl/context/2026-02.html EVENT_ID=2026-02
   ```
   Output: `etl/dist/events/2026-02.json`

2. **Build frontend**:
   ```bash
   make build
   ```

3. **Deploy**: GitHub Pages serves `frontend/dist/`

## Available Commands

Run `make help` to see all available commands, or use:

```bash
# ETL
make etl-install          # Install Python deps
make etl-parse            # Parse event
make etl-lint             # Lint Python code
make etl-add PKG=requests # Add Python package

# Frontend
make frontend-install     # Install Node deps
make dev                  # Start dev server
make build                # Build for production
make frontend-add PKG=vue # Add Node package
```

## Development

**For ETL work**, you can also work directly in the `etl/` directory:
```bash
cd etl
uv add requests          # Add Python package
uv run scripts/parse_event.py context/2026-02.html 2026-02
```

**For frontend work**, you can also work directly in the `frontend/` directory:
```bash
cd frontend
npm add vue             # Add Node package
npm run dev             # Start dev server
```

## Project Overview

Galaxy Stats is built with:
- **Astro**: Static site generator
- **Starlight**: Astro documentation theme
- **Vue**: For interactive components
- **Python**: Data processing (HTML → JSON)

The data pipeline extracts tournament statistics from galaxy.fun HTML files and displays them in a documentation-style website.
