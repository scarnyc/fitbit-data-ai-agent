# gemini_api.py
import os
import google.generativeai as genai
import json

# Configure API key
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

# Configure the Gemini API with specific settings for Gemma 3 27b
genai.configure(api_key=API_KEY)

class FitbitDataExtractor:
    def __init__(self):
        """Initialize the Fitbit data extractor with Gemma 3 27b model.
        Uses the Gemini API to access Gemma 3 27b.
        """
        # Initialize the model with Gemma 3 27b specifically
        self.model = genai.GenerativeModel('gemma-3-27b-it')
    
    def extract_fitbit_metrics(self, email_content):
        """
        Extract Fitbit metrics from email content using Gemini LLM.
        
        Args:
            email_content (str): The raw email content from Fitbit weekly report
            
        Returns:
            dict: Structured data with extracted Fitbit metrics
        """
        prompt = self._construct_extraction_prompt(email_content)
        
        try:
            response = self.model.generate_content(prompt)
            # Parse the response to extract the JSON content
            json_str = self._extract_json_from_response(response.text)
            metrics = json.loads(json_str)
            return metrics
        except Exception as e:
            print(f"Error extracting metrics: {e}")
            return self._get_empty_metrics_template()
    
    def _construct_extraction_prompt(self, email_content):
        """
        Create a detailed prompt for the Gemini model to extract Fitbit metrics.
        
        Args:
            email_content (str): The raw email content
            
        Returns:
            str: Formatted prompt for the model
        """
        return f"""
        You are a specialized data extraction agent focused on Fitbit weekly reports. 
        Extract the following metrics from this Fitbit weekly report email content:
        
        1. Date Range (e.g., Mar. 3 - Mar. 9)
        2. Number of Days Daily Step Target was Met (if available)
        3. Best Day Steps Count (the highest number)
        4. Total Steps that Week
        5. Average Steps per Day
        6. Variance in Total Steps compared to last week (include the direction, e.g., "+500" or "-200")
        7. Total Miles
        8. Variance in Miles compared to last week (include the direction)
        9. Average Daily Calorie Burn
        10. Variance in Calorie Burn compared to last week (include the direction)
        11. Total Active Zone Minutes
        12. Variance in Active Zone Minutes compared to last week (include the direction)
        13. Average Restful Sleep (in hours and minutes)
        14. Variance in Restful Sleep compared to last week (include the direction)
        15. Average Hours with 250+ Steps
        16. Variance in Hours with 250+ Steps compared to last week (include the direction)
        17. Average Resting Heart Rate (in bpm)
        18. Variance in Resting Heart Rate compared to last week (include the direction)
        
        For variances, extract the numeric value and direction. 
        When the report says "same as previous week", report "0" or "same" as appropriate.
        
        Format your response ONLY as a valid JSON object with these exact keys:
        
        {
            "date_range": "",
            "step_target_days_met": null,
            "best_day_steps": null,
            "total_steps": null,
            "avg_steps_per_day": null,
            "steps_variance": "",
            "total_miles": null,
            "miles_variance": "",
            "avg_daily_calorie_burn": null,
            "calorie_burn_variance": "",
            "total_active_zone_minutes": null,
            "active_zone_minutes_variance": "",
            "avg_restful_sleep": "",
            "restful_sleep_variance": "",
            "avg_hours_with_250_steps": null,
            "hours_with_250_steps_variance": "",
            "avg_resting_heart_rate": null,
            "resting_heart_rate_variance": ""
        }
        
        For any metric not found, keep the value null.
        Don't include any explanatory text, just return the JSON object.
        
        Email content:
        {email_content}
        """
    
    def _extract_json_from_response(self, response_text):
        """
        Extract the JSON object from the model's response text.
        
        Args:
            response_text (str): The raw text response from the model
            
        Returns:
            str: The JSON string
        """
        # Try to find JSON object in the response
        try:
            # Look for content between curly braces
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                return response_text[start_idx:end_idx]
            
            # If no JSON object is found, return an empty metrics template
            return json.dumps(self._get_empty_metrics_template())
        except Exception:
            return json.dumps(self._get_empty_metrics_template())
    
    def _get_empty_metrics_template(self):
        """
        Return an empty template for Fitbit metrics.
        
        Returns:
            dict: Empty metrics template
        """
        return {
            "date_range": "",
            "step_target_days_met": None,
            "best_day_steps": None,
            "total_steps": None,
            "avg_steps_per_day": None,
            "steps_variance": "",
            "total_miles": None,
            "miles_variance": "",
            "avg_daily_calorie_burn": None,
            "calorie_burn_variance": "",
            "total_active_zone_minutes": None,
            "active_zone_minutes_variance": "",
            "avg_restful_sleep": "",
            "restful_sleep_variance": "",
            "avg_hours_with_250_steps": None,
            "hours_with_250_steps_variance": "",
            "avg_resting_heart_rate": None,
            "resting_heart_rate_variance": ""
        }
    
    def plan_gmail_automation_steps(self, search_query="subject:\"Your weekly progress report from Fitbit!\" after:2024/06/01"):
        """
        Generate a plan for Gmail automation using the Gemini model.
        
        Args:
            search_query (str): The Gmail search query to use
            
        Returns:
            list: A list of steps to automate Gmail interaction
        """
        prompt = f"""
        Create a detailed, step-by-step plan for automating Gmail interactions to extract Fitbit data.
        The automation will use browser-use/web-ui tool for browser control.
        
        Here's what needs to be done:
        1. Navigate to Gmail
        2. Wait for user login
        3. After login, search for emails with this query: {search_query}
        4. Extract data from each email that matches
        
        For each step, provide:
        - The exact browser automation command
        - Any selectors needed (like CSS selectors or XPath)
        - Error handling guidance
        
        Format as a structured JSON object containing an array of steps.
        """
        
        try:
            response = self.model.generate_content(prompt)
            plan = self._extract_json_from_response(response.text)
            return json.loads(plan)
        except Exception as e:
            print(f"Error generating automation plan: {e}")
            return {
                "steps": [
                    {"action": "navigate", "url": "https://gmail.com"},
                    {"action": "wait_for_login", "selector": "div[role='main']"},
                    {"action": "search", "query": search_query},
                    {"action": "extract_emails", "selector": "tr.zA"}
                ]
            }

# Example usage
if __name__ == "__main__":
    # Sample email content for testing
    sample_email = """
    Hi, Will S.!
    Here are your stats for Mar. 3 - Mar. 9
    Stay Healthy
    We're here for you today and every day. To support you, we made 40+ workouts and mindfulness
    sessions free for all. Or, start a Premium free trial to unlock even more inspiration.
    Unlock the full library of at-home Premium resources with a free trial.
    Mon. Tue. Wed. Thurs. Fri. Sat. Best Day!
    10,834
    44,517 total steps
    Avg. 6,360 steps per day. ▼2,693 fewer than last week
    1 of 2 3/12/25, 6:25 PM
    Gmail - Your weekly progress report from Fitbit! https://mail.google.com/mail/u/0/?ik=9f05aebda1&view=pt&search=al...
    19.02
    2,397
    272
    total miles
    avg. daily calorie burn
    total active zone minutes
    ▼ 1.02 miles below last week
    ▲ 4 cals. over last week
    ▼ 8 min since last week
    7 hrs 52 min
    3 of 9 hrs
    64 bpm
    avg. restful sleep
    avg. hrs with 250+ steps
    avg. resting heart rate
    ▼ 0 hrs 23 min lower than last week
    ▼ 1 hr lower than last week
    same as previous week
    0.0 lb
    no weight change
    same as previous week
    """
    
    # Using Gemma 3 27b via the Gemini API
    extractor = FitbitDataExtractor()
    metrics = extractor.extract_fitbit_metrics(sample_email)
    print(json.dumps(metrics, indent=2))
