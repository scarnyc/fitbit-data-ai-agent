# main.py
import os
import logging
from dotenv import load_dotenv
from routes import app
from database import FitbitDatabase

# Import both agent framework options - we'll try the alternative if standard fails
try:
    from agent_framework import FitbitAgentSystem
    AGENT_IMPLEMENTATION = "standard"
except ImportError:
    try:
        from agent_framework_alt import FitbitAgentSystem
        AGENT_IMPLEMENTATION = "alternative"
    except ImportError:
        AGENT_IMPLEMENTATION = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fitbit_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Load environment variables and initialize required components."""
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Check for required environment variables
    required_vars = ["GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your environment or in a .env file.")
        exit(1)

    # Initialize database
    db = FitbitDatabase()

    # Test agent framework initialization
    if AGENT_IMPLEMENTATION:
        try:
            agent_system = FitbitAgentSystem()
            logger.info(f"Agent framework initialized successfully (using {AGENT_IMPLEMENTATION} implementation)")
        except Exception as e:
            logger.error(f"Error initializing agent framework: {e}")

            # If using standard implementation, try the alternative
            if AGENT_IMPLEMENTATION == "standard":
                try:
                    from agent_framework_alt import FitbitAgentSystem as FitbitAgentSystemAlt
                    agent_system = FitbitAgentSystemAlt()
                    logger.info("Successfully fell back to alternative agent implementation")

                    # Update the routes module to use the alternative implementation
                    import routes
                    routes.FitbitAgentSystem = FitbitAgentSystemAlt
                except Exception as alt_e:
                    logger.error(f"Error initializing alternative agent framework: {alt_e}")
                    logger.error("Please check your Gemini API key and internet connection.")
                    exit(1)
            else:
                logger.error("Please check your Gemini API key and internet connection.")
                exit(1)
    else:
        logger.error("No agent framework implementation available. Please check your installation.")
        exit(1)

    # Install Playwright browsers if not already installed
    try:
        from playwright.sync_api import sync_playwright
        import subprocess
        import sys

        # Check if browsers are installed
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                browser.close()
            logger.info("Playwright browsers already installed")
        except Exception:
            logger.info("Installing Playwright browsers...")
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            logger.info("Playwright browsers installed successfully")
    except Exception as e:
        logger.error(f"Error setting up Playwright: {e}")
        logger.error("You may need to run 'playwright install' manually.")

def create_agent_framework_alt():
    """Create the alternative agent framework implementation file if it doesn't exist."""
    # Path to the alternative implementation file
    alt_path = "agent_framework_alt.py"

    # Check if the file already exists
    if os.path.exists(alt_path):
        logger.info(f"Alternative agent framework file {alt_path} already exists")
        return

    # Content for the alternative implementation
    alt_content = """# agent_framework_alt.py - An alternative implementation that doesn't use ToolNode
import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

import google.generativeai as genai
from langgraph.graph import StateGraph, END

from tools import BrowserTool, GmailSearchTool, DataExtractionTool, DatabaseTool
from database import FitbitDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_framework_alt')

@dataclass
class AgentState:
    \"\"\"State object for the agent system.\"\"\"
    start_date: str = ""
    callback: Optional[Any] = None
    status: str = ""
    plan: str = ""
    search_query: str = ""
    user_logged_in: bool = False
    emails_found: bool = False
    extracted_data: List = field(default_factory=list)
    saved_records: List = field(default_factory=list)
    error: str = ""
    summary: str = ""
    browser_tool: Optional[Any] = None
    gmail_tool: Optional[Any] = None
    extractor_tool: Optional[Any] = None
    database_tool: Optional[Any] = None
    gemma_model: Optional[Any] = None
    page: Optional[Any] = None

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

class FitbitAgentSystem:
    \"\"\"LangGraph-based agent framework for Fitbit data extraction.\"\"\"

    def __init__(self, api_key: str = None):
        \"\"\"
        Initialize the Fitbit agent system.

        Args:
            api_key: Gemini API key for accessing Gemma 3 27b model
        \"\"\"
        # Configure Gemini API
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided")

        genai.configure(api_key=self.api_key)
        self.gemma_model = genai.GenerativeModel('gemma-3-27b-it')

        # Initialize database
        self.db = FitbitDatabase()

        # Define tools
        self.browser_tool = BrowserTool()
        self.gmail_tool = GmailSearchTool()
        self.extractor_tool = DataExtractionTool(self.gemma_model)
        self.database_tool = DatabaseTool(self.db)

        # Build agent graph
        self.graph = self._build_graph()

    def _planning_agent(self, state: AgentState) -> AgentState:
        \"\"\"Create an execution plan for Fitbit data extraction.\"\"\"
        logger.info("Planning agent: creating an extraction plan")

        # Get parameters
        start_date = state.get("start_date", "2024/06/01")

        # Use Gemma 3 to create a plan
        prompt = f\"\"\"
        Create a detailed plan to extract Fitbit data from Gmail emails.

        The goal is to:
        1. Navigate to Gmail
        2. Wait for user login
        3. Search for Fitbit weekly reports (from {start_date} to present)
        4. Extract fitness metrics from each email
        5. Store the data in a database

        Format the plan as a step-by-step process.
        \"\"\"

        try:
            response = state.gemma_model.generate_content(prompt)
            state.plan = response.text
            state.status = "plan_created"
            state.search_query = f"subject:\\"Your weekly progress report from Fitbit!\\" after:{start_date}"

            return state
        except Exception as e:
            logger.error(f"Planning agent error: {e}")
            state.error = str(e)
            state.status = "plan_failed"
            return state

    def _browser_agent(self, state: AgentState) -> AgentState:
        \"\"\"Control the browser to navigate to Gmail and login.\"\"\"
        logger.info("Browser agent: opening browser and navigating to Gmail")

        try:
            # Open the browser
            result = state.browser_tool.execute("open", {"headless": False})
            if not result.get("success", False):
                state.error = result.get("error", "Failed to open browser")
                state.status = "browser_failed"
                return state

            # Navigate to Gmail
            result = state.browser_tool.execute("navigate", {"url": "https://gmail.com"})
            if not result.get("success", False):
                state.error = result.get("error", "Failed to navigate to Gmail")
                state.status = "navigation_failed"
                return state

            # Wait for user login
            result = state.browser_tool.execute("wait_for_login", {})
            state.user_logged_in = result.get("user_logged_in", False)
            state.page = state.browser_tool.page

            if not state.user_logged_in:
                state.error = result.get("error", "Login failed or timed out")
                state.status = "login_failed"
            else:
                state.status = "login_successful"

            return state
        except Exception as e:
            logger.error(f"Browser agent error: {e}")
            state.error = str(e)
            state.status = "browser_error"
            return state

    def _gmail_agent(self, state: AgentState) -> AgentState:
        \"\"\"Search for Fitbit emails in Gmail.\"\"\"
        logger.info("Gmail agent: searching for Fitbit emails")

        try:
            # Use the page object from the browser agent
            search_params = {
                "page": state.page,
                "query": state.search_query
            }

            result = state.gmail_tool.execute("search", search_params)
            state.emails_found = result.get("emails_found", False)

            if not state.emails_found:
                state.error = "No Fitbit emails found"
                state.status = "no_emails_found"
            else:
                state.status = "emails_found"
                state.email_count = result.get("email_count", 0)

            return state
        except Exception as e:
            logger.error(f"Gmail agent error: {e}")
            state.error = str(e)
            state.status = "gmail_error"
            return state

    def _extraction_agent(self, state: AgentState) -> AgentState:
        \"\"\"Extract Fitbit data from the found emails.\"\"\"
        logger.info("Extraction agent: extracting data from emails")

        try:
            extraction_params = {
                "page": state.page,
                "max_emails": 10,  # Limit to 10 emails for testing
                "callback": state.callback
            }

            result = state.extractor_tool.execute("extract_from_emails", extraction_params)
            state.extracted_data = result.get("extracted_data", [])

            if not state.extracted_data:
                state.error = "Failed to extract data from emails"
                state.status = "extraction_failed"
            else:
                state.status = "extraction_successful"

            return state
        except Exception as e:
            logger.error(f"Extraction agent error: {e}")
            state.error = str(e)
            state.status = "extraction_error"
            return state

    def _database_agent(self, state: AgentState) -> AgentState:
        \"\"\"Save extracted data to the database.\"\"\"
        logger.info("Database agent: saving data to database")

        try:
            db_params = {
                "metrics": state.extracted_data
            }

            result = state.database_tool.execute("save_metrics", db_params)
            state.saved_records = result.get("saved_records", [])

            if not state.saved_records:
                state.error = "Failed to save data to database"
                state.status = "database_failed"
            else:
                state.status = "database_successful"

            return state
        except Exception as e:
            logger.error(f"Database agent error: {e}")
            state.error = str(e)
            state.status = "database_error"
            return state

    def _results_agent(self, state: AgentState) -> AgentState:
        \"\"\"Process final results and create a summary.\"\"\"
        logger.info("Results agent: summarizing extraction results")

        try:
            # Generate a summary
            prompt = f\"\"\"
            Create a summary of the Fitbit data extraction process:

            - {len(state.extracted_data)} emails were processed
            - {len(state.saved_records)} records were saved to the database

            Highlight any trends or patterns in the data.
            \"\"\"

            response = state.gemma_model.generate_content(prompt)
            state.summary = response.text
            state.status = "complete"

            # Close the browser if it's open
            if hasattr(state.browser_tool, "browser") and state.browser_tool.browser:
                state.browser_tool.execute("close", {})

            return state
        except Exception as e:
            logger.error(f"Results agent error: {e}")
            state.error = str(e)
            state.status = "results_error"

            # Make sure browser is closed even if there's an error
            if hasattr(state.browser_tool, "browser") and state.browser_tool.browser:
                state.browser_tool.execute("close", {})

            return state

    def _build_graph(self) -> StateGraph:
        \"\"\"Build the agent workflow graph.\"\"\"
        # Create state graph
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("planner", self._planning_agent)
        graph.add_node("browser_agent", self._browser_agent)
        graph.add_node("gmail_agent", self._gmail_agent)
        graph.add_node("extraction_agent", self._extraction_agent)
        graph.add_node("database_agent", self._database_agent)
        graph.add_node("results_agent", self._results_agent)

        # Define conditional routing
        def route_from_browser(state):
            # After login, go to Gmail agent
            if state.get("user_logged_in", False):
                return "gmail_agent"
            # If login failed, end the process
            return END

        def route_from_gmail(state):
            # If emails found, go to extraction agent
            if state.get("emails_found", False):
                return "extraction_agent"
            # If no emails found, end the process
            return END

        # Connect nodes with edges
        graph.add_edge("planner", "browser_agent")
        graph.add_conditional_edges(
            "browser_agent",
            route_from_browser
        )
        graph.add_conditional_edges(
            "gmail_agent",
            route_from_gmail
        )
        graph.add_edge("extraction_agent", "database_agent")
        graph.add_edge("database_agent", "results_agent")
        graph.add_edge("results_agent", END)

        # Compile graph
        return graph.compile()

    def run(self, start_date: str = "2024/06/01", callback=None) -> Dict[str, Any]:
        \"\"\"
        Run the Fitbit agent system.

        Args:
            start_date: Start date for email search (format: YYYY/MM/DD)
            callback: Optional callback function for progress updates

        Returns:
            Dict containing the final state
        \"\"\"
        # Initial state
        initial_state = AgentState(
            start_date=start_date,
            callback=callback,
            status="starting",
            browser_tool=self.browser_tool,
            gmail_tool=self.gmail_tool,
            extractor_tool=self.extractor_tool,
            database_tool=self.database_tool,
            gemma_model=self.gemma_model
        )

        # Run the agent graph
        try:
            logger.info(f"Starting Fitbit agent system with start date {start_date}")
            final_state = self.graph.invoke(initial_state)
            logger.info(f"Agent system completed with status: {final_state.get('status')}")

            # Convert dataclass to dict for return
            result = {
                "status": final_state.status,
                "summary": final_state.summary,
                "error": final_state.error,
                "extracted_data": final_state.extracted_data,
                "saved_records": final_state.saved_records
            }

            return result
        except Exception as e:
            logger.error(f"Agent system error: {e}")
            return {"status": "error", "error": str(e)}
"""

    # Write the content to the file
    with open(alt_path, "w") as f:
        f.write(alt_content)

    logger.info(f"Created alternative agent framework file: {alt_path}")

def main():
    """Main entry point for the application."""
    logger.info("Starting Fitbit Data Extraction Agent")

    # Setup environment
    setup_environment()

    # Create the alternative agent framework file if it doesn't exist
    create_agent_framework_alt()

    # Start the Flask application
    port = int(os.environ.get("PORT", 5000))

    logger.info(f"Application starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()