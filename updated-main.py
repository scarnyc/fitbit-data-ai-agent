# main.py
import os
import logging
from dotenv import load_dotenv
from routes import app
from database import FitbitDatabase
from agent_framework import FitbitAgentSystem

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
    try:
        agent_system = FitbitAgentSystem()
        logger.info("Agent framework initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing agent framework: {e}")
        logger.error("Please check your Gemini API key and internet connection.")
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

def main():
    """Main entry point for the application."""
    logger.info("Starting Fitbit Data Extraction Agent")
    
    # Setup environment
    setup_environment()
    
    # Start the Flask application
    port = int(os.environ.get("PORT", 5000))
    
    logger.info(f"Application starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()
