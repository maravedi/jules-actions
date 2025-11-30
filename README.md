# Jules Planner

A Python package and GitHub Action for integrating [Jules](https://jules.google.com) architecture planning into your development workflow.

## Overview

This package simplifies interfacing with the Jules API from GitHub Actions. It allows you to automatically generate architecture and implementation plans for issues and pull requests directly within GitHub.

## Installation

```bash
pip install jules-planner
```

## Usage

### As a GitHub Action

This package is designed to be used primarily within a GitHub Actions workflow.

1.  **Set up secrets:**
    *   `JULES_API_KEY`: Your Jules API key (Get it from [Jules Settings](https://jules.google.com/settings#api)).
    *   `GITHUB_TOKEN`: Automatically provided by GitHub Actions.

2.  **Create a workflow file:** (e.g., `.github/workflows/jules-plan.yml`)

    ```yaml
    name: Jules Architecture Planning

    on:
      issue_comment:
        types: [created]

    permissions:
      contents: read
      issues: write
      pull-requests: write

    jobs:
      plan:
        if: contains(github.event.comment.body, '@jules plan')
        runs-on: ubuntu-latest
        steps:
          - name: Checkout code
            uses: actions/checkout@v3

          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.10'

          - name: Install Jules Planner
            run: pip install jules-planner

          - name: Generate Plan
            env:
              JULES_API_KEY: ${{ secrets.JULES_API_KEY }}
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            run: jules-planner
    ```

### As a Python Library

You can also use the client directly in your Python scripts:

```python
from jules_planner import JulesPlanner

planner = JulesPlanner(
    api_key="your-api-key",
    repo_owner="owner",
    repo_name="repo"
)

# ... use planner methods ...
```

## Configuration

The CLI tool expects the following environment variables:

*   `JULES_API_KEY`: Required. Your Jules API key.
*   `GITHUB_REPOSITORY`: The repository name in `owner/repo` format (automatically set in GitHub Actions).
*   `GITHUB_EVENT_PATH`: Path to the event payload file (automatically set in GitHub Actions).
*   `GITHUB_TOKEN`: GitHub token for API access (automatically set in GitHub Actions).

## License

MIT
