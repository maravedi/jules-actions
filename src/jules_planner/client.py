import time
import requests
from typing import Dict, Any, Optional, List

class JulesPlanner:
    """Client for Jules API planning requests."""

    def __init__(self, api_key: str, repo_owner: str, repo_name: str):
        """Initialize Jules planner with API key and repository info."""
        if not api_key:
            raise ValueError("JULES_API_KEY is required")

        self.api_key = api_key
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        # Official Jules API base URL
        self.base_url = "https://jules.googleapis.com/v1alpha"
        self.headers = {
            "X-Goog-Api-Key": api_key,
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request to Jules API."""
        url = f"{self.base_url}/{endpoint}"
        kwargs.setdefault('headers', {}).update(self.headers)
        kwargs.setdefault('timeout', 60)

        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def list_sources(self) -> List[Dict[str, Any]]:
        """List available sources (GitHub repositories)."""
        response = self._make_request("GET", "sources")
        data = response.json()
        return data.get("sources", [])

    def find_source(self) -> Optional[str]:
        """Find the source name for the current repository."""
        sources = self.list_sources()

        for source in sources:
            github_repo = source.get("githubRepo", {})
            if (github_repo.get("owner") == self.repo_owner and
                github_repo.get("repo") == self.repo_name):
                return source.get("name")

        return None

    def create_session(self, prompt: str, source_name: str, title: str = "Architecture Planning") -> Dict[str, Any]:
        """Create a new Jules session."""
        payload = {
            "prompt": prompt,
            "sourceContext": {
                "source": source_name,
                "githubRepoContext": {
                    "startingBranch": "main"
                }
            },
            "title": title,
            "requirePlanApproval": False  # Auto-approve plans for API sessions
        }

        response = self._make_request("POST", "sessions", json=payload)
        return response.json()

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details."""
        response = self._make_request("GET", f"sessions/{session_id}")
        return response.json()

    def list_activities(self, session_id: str, page_size: int = 50) -> List[Dict[str, Any]]:
        """List activities in a session."""
        response = self._make_request("GET", f"sessions/{session_id}/activities?pageSize={page_size}")
        data = response.json()
        return data.get("activities", [])

    def wait_for_plan(self, session_id: str, max_wait: int = 120) -> Optional[str]:
        """
        Wait for Jules to generate a plan and extract it.

        Args:
            session_id: The session ID to monitor
            max_wait: Maximum seconds to wait

        Returns:
            The generated plan as markdown, or None if not found
        """
        start_time = time.time()
        plan_text = None

        while (time.time() - start_time) < max_wait:
            activities = self.list_activities(session_id)

            # Look for plan generation activity
            for activity in activities:
                if "planGenerated" in activity:
                    plan = activity["planGenerated"].get("plan", {})
                    steps = plan.get("steps", [])

                    if steps:
                        # Format plan steps as markdown
                        plan_lines = ["## 📋 Implementation Plan\n"]
                        for step in steps:
                            step_num = step.get("index", 0) + 1
                            title = step.get("title", "")
                            plan_lines.append(f"{step_num}. **{title}**")

                        plan_text = "\n".join(plan_lines)

                # Also collect progress updates and other insights
                if "progressUpdated" in activity:
                    pass
                    # Could append progress updates to plan if needed

                # Check if session completed
                if "sessionCompleted" in activity:
                    break

            if plan_text:
                break

            time.sleep(5)  # Poll every 5 seconds

        return plan_text

    def _build_planning_prompt(self, context: Dict[str, Any]) -> str:
        """Build the planning prompt from context."""
        issue_title = context.get("title", "")
        issue_body = context.get("body", "")
        comment_body = context.get("comment", "")
        issue_number = context.get("number", "")
        is_pr = context.get("is_pr", False)

        entity_type = "Pull Request" if is_pr else "Issue"

        prompt = f"""Create a detailed architecture and implementation plan for the following request.

**{entity_type} #{issue_number}: {issue_title}**

**Description:**
{issue_body}

**Planning Request:**
{comment_body}

Please provide a comprehensive architecture and design plan that includes:

1. **Architecture Overview**
   - High-level system design
   - Key components and their interactions
   - Data flow diagrams (in text/markdown format)

2. **Technology Stack Recommendations**
   - Recommended technologies and frameworks
   - Justification for each choice
   - Alternatives considered

3. **Implementation Strategy**
   - Phased implementation approach
   - Key milestones and deliverables
   - Dependencies and prerequisites

4. **Design Decisions**
   - Critical architectural decisions
   - Trade-offs and rationale
   - Scalability considerations

5. **Security & Performance**
   - Security considerations
   - Performance optimization strategies
   - Monitoring and observability approach

6. **Risk Analysis**
   - Potential risks and challenges
   - Mitigation strategies
   - Fallback options

7. **Next Steps**
   - Immediate action items
   - Long-term roadmap
   - Success criteria

Format your response in clear, well-structured Markdown. Use diagrams (ASCII/text-based), tables, and code examples where appropriate.

Focus on practical, actionable recommendations that can guide the development team.
"""

        return prompt

    def generate_plan(self, context: Dict[str, Any]) -> str:
        """
        Generate architecture/design plan based on context.

        Args:
            context: Dictionary containing issue/PR details

        Returns:
            Generated plan as markdown string
        """
        try:
            # Find the source for this repository
            print("🔍 Looking for repository in Jules sources...")
            source_name = self.find_source()

            if not source_name:
                return f"""❌ **Repository Not Found**

The repository `{self.repo_owner}/{self.repo_name}` is not connected to Jules.

**To fix this:**
1. Go to [Jules web app](https://jules.google.com)
2. Install the Jules GitHub app for this repository
3. Once installed, try `@jules plan` again

For more information, see the [Jules documentation](https://jules.google/docs)."""

            print(f"✓ Found source: {source_name}")

            # Build the planning prompt
            prompt = self._build_planning_prompt(context)

            # Create a session
            print("📝 Creating Jules planning session...")
            session_title = f"Architecture Plan: {context.get('title', 'Issue')}"
            session = self.create_session(prompt, source_name, session_title)
            session_id = session.get("id")

            print(f"✓ Session created: {session_id}")

            # Wait for the plan to be generated
            print("⏳ Waiting for Jules to generate the plan...")
            plan = self.wait_for_plan(session_id, max_wait=120)

            if not plan:
                # Fallback: get all activities and format them
                print("⚠ No plan found, retrieving session activities...")
                activities = self.list_activities(session_id)

                if activities:
                    plan_parts = ["## 📊 Jules Session Summary\n"]
                    for activity in activities[:10]:  # Limit to first 10 activities
                        if "progressUpdated" in activity:
                            progress = activity["progressUpdated"]
                            title = progress.get("title", "")
                            description = progress.get("description", "")
                            if title:
                                plan_parts.append(f"- **{title}**")
                                if description:
                                    plan_parts.append(f"  {description}\n")

                    plan = "\n".join(plan_parts) if len(plan_parts) > 1 else None

            if not plan:
                return f"""⚠️ **Planning Session Created**

Jules session has been initiated but no plan was generated yet.

View the session progress at: https://jules.google.com

Session ID: `{session_id}`"""

            return plan

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return """❌ **Authentication Error**

The `JULES_API_KEY` is invalid or has expired.

**To fix this:**
1. Go to [Jules Settings](https://jules.google.com/settings#api)
2. Create a new API key
3. Update the `JULES_API_KEY` secret in repository settings

For more information, see the [Jules API documentation](https://developers.google.com/jules/api)."""
            else:
                return f"❌ Error calling Jules API: {e.response.status_code} {e.response.reason}"

        except requests.exceptions.RequestException as e:
            return f"❌ Error calling Jules API: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
