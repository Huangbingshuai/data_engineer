# DataEngineer Agent

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

DataEngineer Agent is an open-source assistant for working with databases through natural language. Explore schemas, ask data questions, generate and run SQL, and connect your data workflows through the CLI, web interface, REST API, or Model Context Protocol (MCP).

## Features

- Explore connected databases and work with their schemas using natural-language questions.
- Generate and execute SQL, inspect results, and build reusable semantic context.
- Use the interactive CLI, browser-based chat, REST API, or MCP server.
- Try the included synthetic retail database and historical California school data.

## Screenshot

![DataEngineer Agent web interface](docs/screenshots/frontend.png)

## Quick start

### Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- An API key for a supported model provider, or an available subscription/OAuth provider

### Install

```bash
git clone https://github.com/Huangbingshuai/data_engineer.git
cd data_engineer
uv sync --frozen
```

### Configure a model and datasource

Create or edit the local `conf/agent.yml`. Git ignores this file so it can hold machine-specific settings and credentials. If you already have a local configuration, merge these entries into it instead of replacing it.

```yaml
agent:
  target: deepseek
  providers:
    deepseek:
      api_key: "YOUR_DEEPSEEK_API_KEY"
  services:
    datasources:
      retail_demo:
        type: duckdb
        uri: duckdb:///sample_data/retail_demo.duckdb
```

Replace the placeholder with your provider key. The project also supports provider environment variables; see [`conf/providers.yml`](conf/providers.yml) for the provider list and [`conf/agent.yml.example`](conf/agent.yml.example) for the full configuration reference. Do not commit real credentials.

### Start the web interface

```bash
uv run dataengineer-cli --web --config conf/agent.yml --datasource retail_demo
```

Open [http://localhost:8501](http://localhost:8501). The web interface and API are served together. Interactive API documentation is at [http://localhost:8501/docs](http://localhost:8501/docs), and the health endpoint is [http://localhost:8501/health](http://localhost:8501/health). Press `Ctrl+C` to stop the server.

## Use the CLI, API, or MCP server

### Interactive CLI

```bash
uv run dataengineer-cli --config conf/agent.yml --datasource retail_demo
```

### REST API

Run the API on the local machine at `127.0.0.1:8000`:

```bash
uv run dataengineer-api \
  --config conf/agent.yml \
  --datasource retail_demo \
  --host 127.0.0.1
```

- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

For background operation, add `--daemon`. Use `--action status` and `--action stop` with the same `--config` value to check or stop it. The default daemon log is `~/.dataengineer/logs/dataengineer-agent-api.log`.

### MCP server

For an MCP client that launches a local process using stdio:

```bash
uv run dataengineer-mcp \
  --config conf/agent.yml \
  --datasource retail_demo \
  --transport stdio
```

The server also supports HTTP and SSE transports. Run `uv run dataengineer-mcp --help` to see transport and binding options.

## Sample data

| Dataset | Description |
| --- | --- |
| [`retail_demo.duckdb`](sample_data/retail_demo.duckdb) | Deterministic synthetic Brazilian marketplace data with 10,000 orders and fictional records. Rebuild with `uv run python scripts/create_retail_demo_db.py`; the script refuses to overwrite an existing file. |
| [`california_schools_real.duckdb`](sample_data/california_schools_real.duckdb) | Historical school-level directory and aggregate education data. See the [dataset notes and sources](sample_data/README_california_schools_real.md). |
| [`duckdb-demo.duckdb`](sample_data/duckdb-demo.duckdb) | Existing DuckDB example database. |

To use another database, add it under `agent.services.datasources` in `conf/agent.yml` and pass its name with `--datasource`.

## Development

Install development dependencies and run the project checks:

```bash
uv sync --frozen --dev
uv run ruff check .
uv run pytest tests/unit_tests
```

Some embedding-related tests may download model files on their first run.

## Project structure

```text
conf/              Example configuration and provider catalog
dataengineer/      Agent, CLI, REST API, MCP server, and integrations
sample_data/       Example databases and dataset notes
scripts/           Data-generation and maintenance scripts
tests/             Unit, integration, and regression tests
```

## License

This project is licensed under the [Apache License 2.0](LICENSE).
