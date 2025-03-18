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
    """Simple implementation of the Fitbit agent system."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Fitbit agent system.
        
        Args:
            api_key: Gemini API key for accessing Gemma 3 27b model
        """
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
        """
        Run the Fitbit data extraction process.
        
        Args:
            start_date: Start date for email search (format: YYYY/MM/DD)
            callback: Optional callback function for progress updates
            
        Returns:
            Dict containing the results
        """
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
            
            search_query = f"subject:\"Your weekly progress report from Fitbit!\" after:{start_date}"
            
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
            summary_prompt = f"""
            Create a summary of the Fitbit data extraction process:
            
            - {len(extracted_data)} emails were processed
            - {len(saved_records)} records were saved to the database
            
            Highlight any trends or patterns in the data.
            """
            
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
