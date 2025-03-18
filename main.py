# main.py
import os
import logging
from dotenv import load_dotenv
from routes import app
from database import FitbitDatabase

# Import different agent framework implementations
AGENT_IMPLEMENTATION = None
try:
    from simple_agent import FitbitAgentSystem
    AGENT_IMPLEMENTATION = "simple"
except ImportError:
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
            
            # Update the routes module to use this implementation
            import routes
            routes.FitbitAgentSystem = FitbitAgentSystem
            
        except Exception as e:
            logger.error(f"Error initializing {AGENT_IMPLEMENTATION} agent framework: {e}")
            
            # Try simple implementation if it's not already being used
            if AGENT_IMPLEMENTATION != "simple":
                try:
                    from simple_agent import FitbitAgentSystem as SimpleAgentSystem
                    agent_system = SimpleAgentSystem()
                    logger.info("Successfully fell back to simple agent implementation")

                    # Update the routes module to use the simple implementation
                    import routes
                    routes.FitbitAgentSystem = SimpleAgentSystem
                except Exception as simple_e:
                    logger.error(f"Error initializing simple agent framework: {simple_e}")
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

def create_simple_agent():
    """Create the simple agent implementation file if it doesn't exist."""
    # Path to the simple implementation file
    simple_path = "simple_agent.py"

    # Check if the file already exists
    if os.path.exists(simple_path):
        logger.info(f"Simple agent file {simple_path} already exists")
        return

    # Content for the simple implementation (abbreviated for brevity)
    simple_content = """
# simple_agent.py - A simplified agent implementation that doesn't rely on LangGraph
import os
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

import google.generativeai as genai

from tools import BrowserTool, GmailSearchTool, DataExtractionTool, DatabaseTool
from database import FitbitDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_agent')

class FitbitAgentSystem:
    \"\"\"Simple implementation of the Fitbit agent system.\"\"\"
    
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
        
    def run(self, start_date: str = "2024/06/01", callback: Optional[Callable] = None) -> Dict[str, Any]:
        \"\"\"
        Run the Fitbit data extraction process.
        
        Args:
            start_date: Start date for email search (format: YYYY/MM/DD)
            callback: Optional callback function for progress updates
            
        Returns:
            Dict containing the results
        \"\"\"
        # Create safe callback wrapper
        def update_status(status, message, progress):
            try:
                if callback:
                    callback({
                        "status": status,
                        "message": message,
                        "progress": progress
                    })
                logger.info(f"Status: {status} - {message} - {progress}%")
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        # Initialize results
        result = {
            "status": "starting",
            "summary": "",
            "error": "",
            "extracted_data": [],
            "saved_records": []
        }
        
        try:
            # Step 1: Planning
            update_status("planning", "Creating extraction plan...", 5)
            
            search_query = f"subject:\\"Your weekly progress report from Fitbit!\\" after:{start_date}"
            
            # Step 2: Open browser
            update_status("browser_open", "Opening browser...", 10)
            
            browser_result = self.browser_tool.execute("open", {"headless": False})
            if not browser_result.get("success", False):
                error_msg = browser_result.get("error", "Failed to open browser")
                update_status("browser_failed", f"Error: {error_msg}", 0)
                result["status"] = "browser_failed"
                result["error"] = error_msg
                return result
            
            # Step 3: Navigate to Gmail
            update_status("navigating", "Navigating to Gmail...", 20)
            
            nav_result = self.browser_tool.execute("navigate", {"url": "https://gmail.com"})
            if not nav_result.get("success", False):
                error_msg = nav_result.get("error", "Failed to navigate to Gmail")
                update_status("navigation_failed", f"Error: {error_msg}", 0)
                result["status"] = "navigation_failed"
                result["error"] = error_msg
                self.browser_tool.execute("close", {})
                return result
            
            # Step 4: Wait for login
            update_status("waiting_for_login", "Please log in to your Gmail account...", 30)
            
            login_result = self.browser_tool.execute("wait_for_login", {})
            user_logged_in = login_result.get("user_logged_in", False)
            
            if not user_logged_in:
                error_msg = login_result.get("error", "Login failed or timed out")
                update_status("login_failed", f"Error: {error_msg}", 0)
                result["status"] = "login_failed"
                result["error"] = error_msg
                self.browser_tool.execute("close", {})
                return result
            
            # Step 5: Search for Fitbit emails
            update_status("searching", f"Searching for Fitbit emails with query: {search_query}", 40)
            
            search_result = self.gmail_tool.execute("search", {
                "page": self.browser_tool.page,
                "query": search_query
            })
            
            emails_found = search_result.get("emails_found", False)
            
            if not emails_found:
                update_status("no_emails", "No Fitbit emails found", 0)
                result["status"] = "no_emails_found"
                result["error"] = "No Fitbit emails found matching the search criteria"
                self.browser_tool.execute("close", {})
                return result
            
            email_count = search_result.get("email_count", 0)
            update_status("emails_found", f"Found {email_count} Fitbit emails", 50)
            
            # Step 6: Extract data from emails
            update_status("extracting", "Extracting data from Fitbit emails...", 60)
            
            extract_result = self.extractor_tool.execute("extract_from_emails", {
                "page": self.browser_tool.page,
                "max_emails": 10,
                "callback": lambda data: update_status(
                    "extracting_email", 
                    data.get("message", "Processing emails..."), 
                    data.get("progress", 60)
                )
            })
            
            extracted_data = extract_result.get("extracted_data", [])
            
            if not extracted_data:
                update_status("extraction_failed", "No data could be extracted from emails", 0)
                result["status"] = "extraction_failed"
                result["error"] = "Failed to extract data from emails"
                self.browser_tool.execute("close", {})
                return result
            
            update_status("extraction_complete", f"Successfully extracted data from {len(extracted_data)} emails", 70)
            result["extracted_data"] = extracted_data
            
            # Step 7: Save to database
            update_status("saving", "Saving extracted data to database...", 80)
            
            db_result = self.database_tool.execute("save_metrics", {
                "metrics": extracted_data
            })
            
            saved_records = db_result.get("saved_records", [])
            
            if not saved_records:
                update_status("save_failed", "Failed to save data to database", 0)
                result["status"] = "database_failed"
                result["error"] = "Failed to save data to database"
                self.browser_tool.execute("close", {})
                return result
            
            update_status("save_complete", f"Successfully saved {len(saved_records)} records to database", 90)
            result["saved_records"] = saved_records
            
            # Step 8: Generate summary
            update_status("summarizing", "Creating summary of extracted data...", 95)
            
            # Use Gemma to create a summary
            summary_prompt = f\"\"\"
            Create a summary of the Fitbit data extraction process:
            
            - {len(extracted_data)} emails were processed
            - {len(saved_records)} records were saved to the database
            
            Highlight any trends or patterns in the data.
            \"\"\"
            
            try:
                summary_response = self.gemma_model.generate_content(summary_prompt)
                summary = summary_response.text
            except Exception as e:
                logger.error(f"Summary generation error: {e}")
                summary = f"Successfully extracted data from {len(extracted_data)} emails and saved {len(saved_records)} records to the database."
            
            result["summary"] = summary
            result["status"] = "complete"
            
            update_status("complete", "Data extraction complete!", 100)
            
            # Close browser
            self.browser_tool.execute("close", {})
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent system error: {error_msg}")
            
            update_status("error", f"Error: {error_msg}", 0)
            
            result["status"] = "error"
            result["error"] = error_msg
            
            # Make sure browser is closed
            try:
                self.browser_tool.execute("close", {})
            except:
                pass
            
            return result
"""

    # Write the content to the file
    with open(simple_path, "w") as f:
        f.write(simple_content)

    logger.info(f"Created simple agent framework file: {simple_path}")

def main():
    """Main entry point for the application."""
    logger.info("Starting Fitbit Data Extraction Agent")

    # Create the simple agent file if it doesn't exist
    create_simple_agent()
    
    # Setup environment
    setup_environment()

    # Start the Flask application
    port = int(os.environ.get("PORT", 3000))

    logger.info(f"Application starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()