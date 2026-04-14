# pipewarden

A lightweight CLI tool to validate and monitor data pipeline health with configurable alerting rules.

---

## Installation

```bash
pip install pipewarden
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewarden.git
cd pipewarden && pip install -e .
```

---

## Usage

Define your pipeline checks in a `warden.yaml` config file:

```yaml
pipelines:
  - name: daily_sales
    source: postgresql://localhost/mydb
    checks:
      - type: row_count
        min: 1000
      - type: null_threshold
        column: revenue
        max_pct: 0.05
    alerts:
      - channel: slack
        webhook: $SLACK_WEBHOOK_URL
```

Then run the warden:

```bash
pipewarden run --config warden.yaml
```

Check a specific pipeline by name:

```bash
pipewarden run --config warden.yaml --pipeline daily_sales
```

View the status of all monitored pipelines:

```bash
pipewarden status
```

---

## Features

- ✅ Row count, null rate, and schema drift checks
- 🔔 Alerting via Slack, email, or webhook
- 📋 Human-readable validation reports
- ⚙️ Simple YAML-based configuration

---

## License

This project is licensed under the [MIT License](LICENSE).