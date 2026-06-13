"""
Jira Service - Create and manage bug tickets.
"""
import os
import httpx
from typing import Optional
from dotenv import load_dotenv
from app.schemas import JiraBugRequest, JiraBugResponse

# Load .env first
load_dotenv()


class JiraService:
    """Service for interacting with Jira API."""

    def __init__(self):
        # Support both old and new variable names
        self.jira_url = os.getenv("JIRA_URL") or os.getenv("JIRA_BASE_URL", "")
        self.jira_email = os.getenv("JIRA_EMAIL", "")
        self.jira_api_token = os.getenv("JIRA_API_TOKEN", "")
        self.default_project = os.getenv("JIRA_DEFAULT_PROJECT") or os.getenv("JIRA_PROJECT_KEY", "")
        self.default_assignee = os.getenv("JIRA_DEFAULT_ASSIGNEE", "")

        # Check if Jira is configured
        self.is_configured = bool(self.jira_email and self.jira_api_token and self.jira_url)

        if self.is_configured:
            print(f"[JiraService] ✅ Configured: URL={self.jira_url}, Project={self.default_project}")
        else:
            print(f"[JiraService] ⚠️  Not configured (email={bool(self.jira_email)}, token={bool(self.jira_api_token)}, url={bool(self.jira_url)})")

        print(f"[JiraService] Initialized: URL={self.jira_url}, Project={self.default_project}, Configured={self.is_configured}")

    def create_bug(
        self,
        title: str,
        description: str,
        test_result: dict,
        assignee: Optional[str] = None
    ) -> JiraBugResponse:
        """
        Create a bug ticket in Jira.

        Args:
            title: Bug title
            description: Detailed description
            test_result: Test result dict with test_name, status, output, error_message
            assignee: Jira username to assign to

        Returns:
            JiraBugResponse with ticket info or error message
        """
        if not self.is_configured:
            # Return mock response when Jira is not configured
            return self._create_mock_bug(title, description, test_result, assignee)

        try:
            # Prepare Jira issue data
            assignee_user = assignee or self.default_assignee

            # Format description with test details
            jira_description = self._format_jira_description(
                title=title,
                description=description,
                test_result=test_result
            )

            payload = {
                "fields": {
                    "project": {"key": self.default_project},
                    "summary": title,
                    "description": jira_description,
                    "issuetype": {"name": "Bug"},  # Use name instead of ID (more reliable)
                    "labels": ["auto-generated", "api-test", "qa-bot"]
                }
            }

            # Add assignee if provided
            if assignee_user:
                payload["fields"]["assignee"] = {"accountId": assignee_user}

            # Create issue
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Basic {self._encode_auth()}"
            }

            url = f"{self.jira_url}/rest/api/3/issue"

            # Debug: print payload for troubleshooting
            print(f"[JiraService] Creating bug: {title}")
            print(f"[JiraService] Payload: {payload}")

            with httpx.Client(timeout=30) as client:
                response = client.post(url, headers=headers, json=payload)

                # Handle error responses with details
                if response.status_code != 201:
                    error_detail = response.text
                    print(f"[JiraService] Error response ({response.status_code}): {error_detail}")
                    return JiraBugResponse(
                        status="error",
                        message=f"Jira API error ({response.status_code}): {error_detail[:500]}"
                    )

                result = response.json()
                ticket_key = result["key"]
                ticket_url = f"{self.jira_url}/browse/{ticket_key}"

                print(f"[JiraService] ✅ Bug created: {ticket_key}")
                return JiraBugResponse(
                    status="success",
                    message=f"Bug ticket created: {ticket_key}",
                    ticket_key=ticket_key,
                    ticket_url=ticket_url
                )

        except httpx.HTTPError as e:
            return JiraBugResponse(
                status="error",
                message=f"Jira HTTP error: {str(e)}"
            )
        except Exception as e:
            return JiraBugResponse(
                status="error",
                message=f"Failed to create bug: {str(e)}"
            )

    def _format_jira_description(self, title: str, description: str, test_result: dict) -> dict:
        """Format description for Jira with ADF (Atlassian Document Format)."""
        # Get test info with safe defaults
        test_name = test_result.get('test_name', 'N/A') or 'N/A'
        status = test_result.get('status', 'N/A') or 'N/A'
        duration = test_result.get('duration', 0) or 0

        # Simplest valid ADF format - plain paragraphs only
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": title}]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": f"Test: {test_name}"}]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": f"Status: {status.upper()}"}]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": f"Duration: {duration:.2f}s"}]
                }
            ]
        }

    def _encode_auth(self) -> str:
        """Encode email:token for Basic auth."""
        import base64
        creds = f"{self.jira_email}:{self.jira_api_token}"
        return base64.b64encode(creds.encode()).decode()

    def _create_mock_bug(
        self,
        title: str,
        description: str,
        test_result: dict,
        assignee: Optional[str] = None
    ) -> JiraBugResponse:
        """
        Create a mock bug response when Jira is not configured.
        Prints the bug details that WOULD be created.
        """
        print("\n" + "="*60)
        print("🐛 MOCK JIRA BUG TICKET (Jira not configured)")
        print("="*60)
        print(f"\n📝 Title: {title}")
        print(f"\n👤 Assignee: {assignee or 'Unassigned'}")
        print(f"\n📋 Description:")
        print(self._format_jira_description(title, description, test_result))
        print("\n" + "="*60)
        print("💡 To enable Jira integration, set these env vars:")
        print("  JIRA_URL=https://your-company.atlassian.net")
        print("  JIRA_EMAIL=your.email@company.com")
        print("  JIRA_API_TOKEN=your_api_token")
        print("  JIRA_DEFAULT_PROJECT=PROJ")
        print("="*60 + "\n")

        return JiraBugResponse(
            status="mock",
            message="Jira not configured - mock ticket generated (see logs)",
            ticket_key="MOCK-123",
            ticket_url="N/A"
        )


# Global instance
jira_service = JiraService()
