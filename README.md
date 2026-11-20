# DataEngineer Agent

DataEngineer Agent is an open-source assistant for exploring databases and completing data-engineering tasks with natural-language instructions. It includes a command-line interface, a browser-based chat interface, a REST API, MCP support, and sample datasets.

## Features

- Ask questions about connected databases in natural language and generate or run SQL.
- Work with supported databases through configured datasources.
- Use the interactive CLI, the web chat interface, or the HTTP API.
- Connect the agent to MCP clients with the included MCP server.
- Explore the included synthetic retail demo and historical California school statistics.

## Screenshots

![DataEngineer Agent web interface](docs/screenshots/frontend.png)

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- An API key for a supported model provider, unless using a subscription or OAuth provider

## Quick start

### 1. Get the code and install dependencies

```bash
git clone https://github.com/Huangbingshuai/data_engineer.git
cd data_engineer
uv sync --frozen
```

### 2. Configure a model provider and datasource

Create `conf/agent.yml` with your local settings. This file is ignored by Git. The example below uses DeepSeek and the included retail database:

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

Replace the placeholder with your key. For other providers, see the supported provider and model list in [`conf/providers.yml`](conf/providers.yml) and configuration examples in [`conf/agent.yml.example`](conf/agent.yml.example). Keep credentials in your local, ignored configuration and do not commit them.

### 3. Start the web interface

```bash
uv run dataengineer-cli --web --config conf/agent.yml --datasource retail_demo
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501). The web app serves the chat interface and API together. Check [http://127.0.0.1:8501/health](http://127.0.0.1:8501/health) for health status and [http://127.0.0.1:8501/docs](http://127.0.0.1:8501/docs) for interactive API documentation. Press `Ctrl+C` in the terminal to stop the server.

To use the interactive terminal interface instead, run:

```bash
uv run dataengineer-cli --config conf/agent.yml --datasource retail_demo
```

## Run the API server separately

The API server runs on port `8000` by default. Bind it to loopback for local development:

```bash
uv run dataengineer-api \
  --config conf/agent.yml \
  --datasource retail_demo \
  --host 127.0.0.1
```

- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Press `Ctrl+C` to stop a foreground server. See the [API guide](dataengineer/api/README.md) for daemon controls and endpoint examples.

## Sample data

| Dataset | Description | Build or provenance |
| --- | --- | --- |
| `sample_data/retail_demo.duckdb` | Deterministic synthetic Brazilian marketplace data with 10,000 orders. It contains fictional records and does not copy customer records from the public reference dataset. | Rebuild with `uv run python scripts/create_retail_demo_db.py`. The script refuses to overwrite an existing file. |
| `sample_data/california_schools_real.duckdb` | Historical school-level directory, Free or Reduced-Price Meal (FRPM), and SAT summary data. School staff contact fields are omitted. | See [dataset notes](sample_data/README_california_schools_real.md). Rebuild with `uv run python scripts/create_california_schools_db.py`; the script refuses to overwrite an existing file. |
| `sample_data/duckdb-demo.duckdb` | Existing DuckDB example database. | Included in the repository. |

To connect a different database, add another entry under `agent.services.datasources` in `conf/agent.yml` and pass its name with `--datasource`.

## Development

Install the locked development dependencies and run the code checks:

```bash
uv sync --frozen --dev
uv run ruff check .
uv run pytest tests/unit_tests
```

Some embedding-related tests may download model files on first run.

## Project layout

```text
conf/              Example configuration and provider catalog
dataengineer/      Application, CLI, API, and MCP server
sample_data/       Example databases and dataset notes
scripts/           Data-generation and maintenance scripts
tests/             Unit, integration, and regression tests
```

## License

This project is licensed under the [Apache License 2.0](LICENSE).
