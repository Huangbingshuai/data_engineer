# DataEngineer Agent

AI-powered SQL agent for working with databases through natural-language requests. This repository contains the DataEngineer Agent source and a synthetic retail demo database.

## Requirements

- Python 3.12 or newer
- A configured model provider API key

## Local setup

```bash
uv sync --frozen
cp conf/agent.yml.example conf/agent.yml
```

Set the model provider credentials and datasource settings in `conf/agent.yml`. This local configuration is ignored by Git so credentials are not committed.

Start the web app and API together:

```bash
uv run dataengineer-cli --web --config conf/agent.yml --datasource retail_demo --host 127.0.0.1 --port 8501
```

Open <http://127.0.0.1:8501/>. The health endpoint is <http://127.0.0.1:8501/health>.

The `retail_demo` datasource uses the synthetic dataset at `sample_data/retail_demo.duckdb`.

## License

Apache-2.0. See [LICENSE](LICENSE).
