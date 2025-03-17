# Fitbit Data Extraction Agent System

An AI-powered, agent-based application that automatically extracts and organizes Fitbit data from your Gmail using LangGraph for agent orchestration, Gemma 3 27b via the Gemini API, and Playwright for browser control.

## Features

- **Multi-Agent Framework**: Uses LangGraph to coordinate specialized AI agents
- **Automated Gmail Navigation**: Navigates to Gmail and helps you log in
- **Intelligent Email Search**: Automatically finds your Fitbit weekly progress reports 
- **Data Extraction**: Extracts comprehensive fitness metrics from email content
- **Structured Storage**: Organizes all your fitness data in a database with week-over-week comparisons
- **Data Visualization**: View trends and progress in an intuitive dashboard
- **Export Options**: Download your data in CSV or JSON formats
- **Extensible Architecture**: Easily add new agents to extend functionality

## Agent Architecture

The system uses a LangGraph-based multi-agent framework with the following components:

1. **Planning Agent**: Creates an execution plan using Gemma 3 27b
2. **Browser Agent**: Controls the browser for Gmail navigation
3. **Gmail Agent**: Performs email search and selection
4. **Extraction Agent**: Uses Gemma 3 27b to extract structured data from emails
5. **Database Agent**: Stores and retrieves data from the database
6. **Results Agent**: Summarizes the extraction results

## Metrics Tracked

- Date Range
- Daily Step Target Achievement Count
- Best Day Step Count
- Weekly Total Steps
- Average Daily Steps (with variance tracking)
- Total Miles (with variance tracking)
- Average Daily Calorie Burn (with variance tracking)
- Total Active Zone Minutes (with variance tracking)
- Average Restful Sleep (with variance tracking)
- Average Hours with 250+ Steps (with variance tracking)
- Average Resting Heart Rate (with variance tracking)

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Gemini API key (for access to Gemma 3 27b)
- Gmail account with Fitbit weekly reports

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd fitbit-data-extraction-agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

5. Set up environment variables:
   Create a `.env` file in the project root with:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   FLASK_SECRET_KEY=random_secret_key_for_flask
   ```

### Running the Application

1. Start the application:
   ```bash
   python main.py
   ```

2. Open your browser and navigate to `http://localhost:5000`

3. Click "Start Extraction" and follow the prompts

## Extending with New Agents

The agent framework is designed to be easily extensible. To add a new agent:

1. Create a new tool in `tools.py`
2. Add the agent to the graph in `agent_framework.py`
3. Connect it to the existing workflow

Example:

```python
# Add a weather agent to correlate Fitbit activity with weather
weather_tool = WeatherTool()
graph.add_node("weather_agent", ToolNode(weather_tool))
graph.add_edge("extraction_agent", "weather_agent")
graph.add_edge("weather_agent", "database_agent")
```

## Security Notes

- The application never stores your Gmail credentials
- Browser automation is run in a sandboxed environment
- Your data is stored locally in a SQLite database

## Troubleshooting

- **Login Issues**: Make sure you have "Less secure app access" enabled for your Google account or use an app password.
- **No Data Found**: Verify that you have Fitbit weekly progress report emails in your Gmail account.
- **Extraction Errors**: Check that the email format matches what the extractor expects.
- **Agent Framework Errors**: Check the logs for detailed error messages.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
