# agent_framework.py
import os
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

import google.generativeai as genai
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_node import ToolNode

from tools import BrowserTool, GmailSearchTool, DataExtractionTool, DatabaseTool
from database import FitbitDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_framework')

class FitbitAgentSystem:
    """LangGraph-based agent framework for Fitbit data extraction."""
    
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
        self.tools = {
            "browser": BrowserTool(),
            "gmail": GmailSearchTool(),
            "extractor": DataExtractionTool(self.gemma_model),
            "database": DatabaseTool(self.db)
        }
        
        # Build agent graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph."""
        graph = StateGraph()
        
        # Add nodes for different agent functions
        graph.add_node("planner", self._planning_agent)
        graph.add_node("browser_agent", ToolNode(self.tools["browser"]))
        graph.add_node("gmail_agent", ToolNode(self.tools["gmail"]))
        graph.add_node("extraction_agent", ToolNode(self.tools["extractor"]))
        graph.add_node("database_agent", ToolNode(self.tools["database"]))
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
    
    def _planning_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create an execution plan for Fitbit data extraction."""
        logger.info("Planning agent: creating an extraction plan")
        
        # Get parameters
        start_date = state.get("start_date", "2024/06/01")
        
        # Use Gemma 3 to create a plan
        prompt = f"""
        Create a detailed plan to extract Fitbit data from Gmail emails.
        
        The goal is to:
        1. Navigate to Gmail
        2. Wait for user login
        3. Search for Fitbit weekly reports (from {start_date} to present)
        4. Extract fitness metrics from each email
        5. Store the data in a database
        
        Format the plan as a step-by-step process.
        """
        
        try:
            response = self.gemma_model.generate_content(prompt)
            plan = response.text
            
            return {
                **state,
                "plan": plan,
                "status": "plan_created",
                "start_date": start_date,
                "search_query": f"subject:\"Your weekly progress report from Fitbit!\" after:{start_date}"
            }
        except Exception as e:
            logger.error(f"Planning agent error: {e}")
            return {**state, "error": str(e), "status": "plan_failed"}
    
    def _results_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process final results and create a summary."""
        logger.info("Results agent: summarizing extraction results")
        
        extracted_data = state.get("extracted_data", [])
        saved_records = state.get("saved_records", [])
        
        # Generate a summary
        prompt = f"""
        Create a summary of the Fitbit data extraction process:
        
        - {len(extracted_data)} emails were processed
        - {len(saved_records)} records were saved to the database
        
        Highlight any trends or patterns in the data.
        """
        
        try:
            response = self.gemma_model.generate_content(prompt)
            summary = response.text
            
            return {
                **state, 
                "summary": summary,
                "status": "complete"
            }
        except Exception as e:
            logger.error(f"Results agent error: {e}")
            return {
                **state, 
                "summary": f"Extraction complete. {len(saved_records)} records saved to database.",
                "status": "complete"
            }
    
    def run(self, start_date: str = "2024/06/01", callback=None) -> Dict[str, Any]:
        """
        Run the Fitbit agent system.
        
        Args:
            start_date: Start date for email search (format: YYYY/MM/DD)
            callback: Optional callback function for progress updates
            
        Returns:
            Dict containing the final state
        """
        # Initial state
        initial_state = {
            "start_date": start_date,
            "callback": callback,
            "status": "starting"
        }
        
        # Run the agent graph
        try:
            logger.info(f"Starting Fitbit agent system with start date {start_date}")
            final_state = self.graph.invoke(initial_state)
            logger.info(f"Agent system completed with status: {final_state.get('status')}")
            return final_state
        except Exception as e:
            logger.error(f"Agent system error: {e}")
            return {"status": "error", "error": str(e)}

# Example usage
if __name__ == "__main__":
    # Initialize the agent system
    agent_system = FitbitAgentSystem()
    
    # Define a simple callback
    def progress_callback(data):
        print(f"Status: {data.get('status')} - Progress: {data.get('progress', 0)}%")
    
    # Run the system
    result = agent_system.run(callback=progress_callback)
    print(f"Final status: {result.get('status')}")
    if result.get("summary"):
        print(f"Summary: {result.get('summary')}")
