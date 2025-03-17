# tools.py
import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_tools')

class BrowserTool:
    """Tool for browser automation."""
    
    def __init__(self):
        """Initialize the browser tool."""
        self.browser = None
        self.page = None
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a browser automation action.
        
        Args:
            action: The action to perform (open, navigate, wait_for_login, close, auto)
            params: Parameters for the action
            
        Returns:
            Dict containing the result of the action
        """
        logger.info(f"Browser tool: executing {action}")
        
        if action == "open":
            return self._open_browser(params)
        elif action == "navigate":
            return self._navigate(params)
        elif action == "wait_for_login":
            return self._wait_for_login(params)
        elif action == "close":
            return self._close_browser()
        elif action == "auto":
            # Automatic mode for simplified integration
            if not self.browser:
                # First open the browser
                result = self._open_browser({"headless": params.get("headless", False)})
                if not result.get("success", False):
                    return result
                
            # Then navigate to Gmail
            result = self._navigate({"url": "https://gmail.com"})
            if not result.get("success", False):
                return result
                
            # Wait for login
            return self._wait_for_login(params)
        else:
            return {"error": f"Unknown action: {action}", "success": False}
    
    def _open_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a browser instance."""
        try:
            headless = params.get("headless", False)
            
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(
                headless=headless,
                chromium_sandbox=True,
                env={},
                args=[
                    "--disable-extensions",
                    "--disable-file-system"
                ]
            )
            
            self.page = self.browser.new_page()
            self.page.set_viewport_size({"width": 1280, "height": 800})
            
            return {
                "success": True, 
                "message": "Browser opened successfully",
                "browser_open": True
            }
        except Exception as e:
            logger.error(f"Error opening browser: {e}")
            return {"error": str(e), "success": False}
    
    def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL."""
        try:
            url = params.get("url")
            if not url:
                return {"error": "No URL provided", "success": False}
            
            if not self.page:
                return {"error": "Browser not open", "success": False}
            
            self.page.goto(url)
            
            return {
                "success": True, 
                "message": f"Navigated to {url}",
                "current_url": self.page.url
            }
        except Exception as e:
            logger.error(f"Error navigating: {e}")
            return {"error": str(e), "success": False}
    
    def _wait_for_login(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for user to login to Gmail."""
        try:
            if not self.page:
                return {"error": "Browser not open", "success": False}
            
            timeout = params.get("timeout", 300000)  # 5 minutes default
            
            # First check if we're already on the login page
            login_detected = self.page.query_selector("input[type='email']") is not None
            
            if login_detected:
                logger.info("Login page detected, waiting for user to complete login")
                # Wait for the main Gmail interface to appear after login
                self.page.wait_for_selector("div[role='main']", timeout=timeout)
            else:
                # Already logged in or on a different page
                self.page.wait_for_selector("div[role='main']", timeout=10000)
            
            return {
                "success": True, 
                "message": "User logged in successfully",
                "user_logged_in": True
            }
        except Exception as e:
            logger.error(f"Error waiting for login: {e}")
            return {"error": str(e), "success": False, "user_logged_in": False}
    
    def _close_browser(self) -> Dict[str, Any]:
        """Close the browser."""
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
                self.page = None
            
            return {"success": True, "message": "Browser closed successfully"}
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            return {"error": str(e), "success": False}

class GmailSearchTool:
    """Tool for searching Gmail for Fitbit emails."""
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Gmail search action.
        
        Args:
            action: The action to perform (search)
            params: Parameters for the action
            
        Returns:
            Dict containing the result of the action
        """
        logger.info(f"Gmail tool: executing {action}")
        
        if action == "search":
            return self._search_emails(params)
        else:
            return {"error": f"Unknown action: {action}", "success": False}
    
    def _search_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for emails in Gmail."""
        try:
            page = params.get("page")
            if not page:
                # Get page from browser tool
                browser_tool = params.get("browser_tool")
                if browser_tool and hasattr(browser_tool, "page"):
                    page = browser_tool.page
                
            if not page:
                return {"error": "No page provided", "success": False}
            
            search_query = params.get("query") or params.get("search_query")
            if not search_query:
                return {"error": "No search query provided", "success": False}
            
            # Click on search bar
            search_bar = page.query_selector("input[aria-label='Search mail']")
            if search_bar:
                search_bar.click()
                
                # Enter search query
                page.fill("input[aria-label='Search mail']", search_query)
                
                # Submit search
                page.press("input[aria-label='Search mail']", "Enter")
            else:
                # Alternative method if the primary selector doesn't work
                page.click("div[role='search']")
                page.keyboard.type(search_query)
                page.keyboard.press("Enter")
            
            # Wait for search results
            page.wait_for_selector("div[role='main']", timeout=10000)
            
            # Check if we have results
            no_results = page.query_selector("div.TD")
            if no_results and "No results found" in no_results.inner_text():
                return {
                    "success": True,
                    "emails_found": False,
                    "message": "No emails found matching the search criteria"
                }
            
            # Get email elements
            email_elements = page.query_selector_all("tr.zA")
            
            return {
                "success": True,
                "emails_found": len(email_elements) > 0,
                "email_count": len(email_elements),
                "message": f"Found {len(email_elements)} emails matching the search criteria",
                "page": page  # Pass the page object for the next agent
            }
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return {"error": str(e), "success": False, "emails_found": False}

class DataExtractionTool:
    """Tool for extracting Fitbit data from emails."""
    
    def __init__(self, model):
        """
        Initialize the data extraction tool.
        
        Args:
            model: The Gemma model for data extraction
        """
        self.model = model
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a data extraction action.
        
        Args:
            action: The action to perform (extract_from_emails)
            params: Parameters for the action
            
        Returns:
            Dict containing the result of the action
        """
        logger.info(f"Data extraction tool: executing {action}")
        
        if action == "extract_from_emails":
            return self._extract_from_emails(params)
        elif action == "parse_email":
            return self._parse_email(params)
        else:
            return {"error": f"Unknown action: {action}", "success": False}
    
    def _extract_from_emails(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from multiple emails."""
        try:
            # Try to get page from different sources
            page = params.get("page")
            if not page:
                gmail_results = params.get("gmail_results", {})
                page = gmail_results.get("page")
            
            if not page:
                return {"error": "No page provided", "success": False}
            
            max_emails = params.get("max_emails", 10)
            
            # Get email elements
            email_elements = page.query_selector_all("tr.zA")
            if not email_elements:
                return {
                    "success": True,
                    "message": "No emails to process",
                    "extracted_data": []
                }
            
            total_emails = min(len(email_elements), max_emails)
            extracted_data = []
            
            for idx, email in enumerate(email_elements[:max_emails]):
                try:
                    # Report progress
                    callback = params.get("callback")
                    if callback:
                        progress = int((idx / total_emails) * 100)
                        callback({
                            "status": "extracting_data",
                            "message": f"Processing email {idx+1} of {total_emails}",
                            "progress": progress
                        })
                    
                    # Click on the email to open it
                    email.click()
                    page.wait_for_selector("div[role='main']", timeout=10000)
                    
                    # Extract email content
                    content_element = page.query_selector("div[role='main']")
                    if content_element:
                        email_content = content_element.inner_text()
                        
                        # Parse the email content
                        parse_result = self._parse_email({"content": email_content})
                        
                        if parse_result.get("success") and parse_result.get("metrics"):
                            extracted_data.append(parse_result.get("metrics"))
                    
                    # Go back to the inbox
                    page.click("button[aria-label='Back to Inbox']")
                    page.wait_for_selector("div[role='main']", timeout=10000)
                    
                except Exception as e:
                    logger.error(f"Error processing email {idx+1}: {e}")
                    # Try to return to inbox if an error occurs
                    try:
                        page.click("button[aria-label='Back to Inbox']")
                        page.wait_for_selector("div[role='main']", timeout=10000)
                    except:
                        pass
            
            return {
                "success": True,
                "message": f"Extracted data from {len(extracted_data)} emails",
                "extracted_data": extracted_data
            }
        except Exception as e:
            logger.error(f"Error extracting from emails: {e}")
            return {"error": str(e), "success": False, "extracted_data": []}
    
    def _parse_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Fitbit data from an email."""
        try:
            content = params.get("content")
            if not content:
                return {"error": "No content provided", "success": False}
            
            # Use Gemma 3 to extract the metrics
            prompt = f"""
            Extract the following metrics from this Fitbit weekly report email content:
            1. Date Range (e.g., Mar. 3 - Mar. 9)
            2. Number of Days Daily Step Target was Met (if available)
            3. Best Day Steps Count (the highest number)
            4. Total Steps that Week
            5. Average Steps per Day
            6. Variance in Total Steps compared to last week (number with direction)
            7. Total Miles
            8. Variance in Miles compared to last week (number with direction)
            9. Average Daily Calorie Burn
            10. Variance in Calorie Burn compared to last week (number with direction)
            11. Total Active Zone Minutes
            12. Variance in Active Zone Minutes compared to last week (number with direction)
            13. Average Restful Sleep (in hours and minutes)
            14. Variance in Restful Sleep compared to last week (in hours and minutes with direction)
            15. Average Hours with 250+ Steps
            16. Variance in Hours with 250+ Steps compared to last week (number with direction)
            17. Average Resting Heart Rate (in bpm)
            18. Variance in Resting Heart Rate compared to last week (with direction)
            
            Format your response as a JSON object with these exact keys:
            {{
                "date_range": "",
                "step_target_days_met": null,
                "best_day_steps": null,
                "total_steps": null,
                "avg_steps_per_day": null,
                "steps_variance": null,
                "total_miles": null,
                "miles_variance": null,
                "avg_daily_calorie_burn": null,
                "calorie_burn_variance": null,
                "total_active_zone_minutes": null,
                "active_zone_minutes_variance": null,
                "avg_restful_sleep": "",
                "restful_sleep_variance": "",
                "avg_hours_with_250_steps": null,
                "hours_with_250_steps_variance": null,
                "avg_resting_heart_rate": null,
                "resting_heart_rate_variance": ""
            }}
            
            For any metric not found in the email, set the value to null.
            Only return the JSON object, nothing else.
            
            Email content:
            {content}
            """
            
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            json_str = self._extract_json_from_response(response.text)
            metrics = json.loads(json_str)
            
            return {
                "success": True,
                "metrics": metrics
            }
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return {"error": str(e), "success": False}
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON object from response text."""
        try:
            # Look for content between curly braces
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                return response_text[start_idx:end_idx]
            
            # If no JSON object is found, return an empty object
            return "{}"
        except Exception:
            return "{}"

class DatabaseTool:
    """Tool for database operations."""
    
    def __init__(self, db):
        """
        Initialize the database tool.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a database action.
        
        Args:
            action: The action to perform (save_metrics, get_metrics)
            params: Parameters for the action
            
        Returns:
            Dict containing the result of the action
        """
        logger.info(f"Database tool: executing {action}")
        
        if action == "save_metrics":
            return self._save_metrics(params)
        elif action == "get_metrics":
            return self._get_metrics(params)
        else:
            return {"error": f"Unknown action: {action}", "success": False}
    
    def _save_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save metrics to the database."""
        try:
            # Try to get metrics from different sources
            metrics_list = params.get("metrics", [])
            if not metrics_list:
                extraction_results = params.get("extraction_results", {})
                metrics_list = extraction_results.get("extracted_data", [])
                
            if not metrics_list:
                return {
                    "success": True,
                    "message": "No metrics to save",
                    "saved_records": []
                }
            
            saved_records = []
            
            for metrics in metrics_list:
                record_id = self.db.save_metrics(metrics)
                if record_id:
                    saved_records.append(record_id)
            
            return {
                "success": True,
                "message": f"Saved {len(saved_records)} records to database",
                "saved_records": saved_records
            }
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return {"error": str(e), "success": False, "saved_records": []}
    
    def _get_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get metrics from the database."""
        try:
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            
            if start_date and end_date:
                metrics = self.db.get_metrics_by_date_range(start_date, end_date)
            else:
                metrics = self.db.get_all_metrics()
            
            return {
                "success": True,
                "message": f"Retrieved {len(metrics)} records from database",
                "metrics": metrics
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"error": str(e), "success": False, "metrics": []}
