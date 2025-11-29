import os
import json
import sys
import requests
from typing import Dict, Any

def get_issue_context() -> Dict[str, Any]:
    """Extract issue/PR context from GitHub environment variables."""
    # GitHub Actions provides context through environment variables
    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not event_path or not os.path.exists(event_path):
        raise ValueError("GitHub event data not found")

    with open(event_path, 'r') as f:
        event_data = json.load(f)

    # Extract relevant information
    issue = event_data.get("issue", {})
    comment = event_data.get("comment", {})

    return {
        "number": issue.get("number", ""),
        "title": issue.get("title", ""),
        "body": issue.get("body", ""),
        "comment": comment.get("body", ""),
        "is_pr": "pull_request" in issue,
        "author": comment.get("user", {}).get("login", "unknown")
    }


def post_comment_to_github(comment_body: str) -> None:
    """Post the generated plan as a comment on the issue/PR."""
    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not all([github_token, repo, event_path]):
        print("Error: Missing required GitHub environment variables")
        sys.exit(1)

    with open(event_path, 'r') as f:
        event_data = json.load(f)

    issue_number = event_data.get("issue", {}).get("number")

    if not issue_number:
        print("Error: Could not determine issue number")
        sys.exit(1)

    # Post comment using GitHub API
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.post(
        url,
        headers=headers,
        json={"body": comment_body},
        timeout=30
    )

    if response.status_code == 201:
        print("✅ Successfully posted Jules plan to GitHub")
    else:
        print(f"❌ Failed to post comment: {response.status_code} - {response.text}")
        sys.exit(1)
