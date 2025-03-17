# routes.py
from flask import Flask, render_template, jsonify, request, redirect, url_for, make_response
import json
import os
from datetime import datetime
import threading

from agent_framework import FitbitAgentSystem
from database import FitbitDatabase

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fitbit-extraction-app-secret")

# Initialize database
db = FitbitDatabase()

# Store agent results for access across requests
agent_results = {
    "status": "idle",
    "message": "Ready to extract data",
    "progress": 0,
    "last_run": None
}

@app.route('/')
def index():
    """Render the main page of the application."""
    global agent_results
    return render_template('index.html', status=agent_results)

@app.route('/start-extraction', methods=['POST'])
def start_extraction():
    """
    Start the Fitbit data extraction process using the agent framework.
    """
    global agent_results
    
    try:
        # Get parameters from request
        start_date = request.form.get('start_date', '2024/06/01')
        
        # Update status
        agent_results = {
            "status": "starting",
            "message": "Initializing agent system...",
            "progress": 5,
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Define progress callback function
        def progress_callback(data):
            global agent_results
            
            status = data.get('status', 'running')
            message = data.get('message', 'Processing...')
            progress = data.get('progress', agent_results["progress"])
            
            # Update the global status
            agent_results = {
                "status": status,
                "message": message,
                "progress": progress,
                "last_run": agent_results["last_run"]
            }
        
        # Start agent process in a separate thread
        def run_agent_process():
            global agent_results
            
            try:
                # Initialize agent system
                agent_system = FitbitAgentSystem()
                
                # Run the agent system
                result = agent_system.run(start_date=start_date, callback=progress_callback)
                
                # Update final status
                agent_results = {
                    "status": result.get("status", "complete"),
                    "message": result.get("summary", "Extraction complete"),
                    "progress": 100,
                    "last_run": agent_results["last_run"],
                    "data_count": len(result.get("saved_records", []))
                }
            except Exception as e:
                agent_results = {
                    "status": "error",
                    "message": f"Error: {str(e)}",
                    "progress": 0,
                    "last_run": agent_results["last_run"]
                }
        
        # Start the thread
        thread = threading.Thread(target=run_agent_process)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "started",
            "message": "Agent process started. Check status endpoint for updates."
        })
    except Exception as e:
        agent_results = {
            "status": "error",
            "message": f"Error: {str(e)}",
            "progress": 0,
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return jsonify({"status": "error", "message": str(e)})

@app.route('/status')
def get_status():
    """Get the current status of the agent process."""
    global agent_results
    return jsonify(agent_results)

@app.route('/view-data')
def view_data():
    """
    Display the extracted Fitbit data.
    
    Renders a page showing all extracted Fitbit metrics in a table
    with visualizations.
    """
    # Get data from database
    metrics = db.get_all_metrics()
    
    # Convert dates for better display if needed
    for metric in metrics:
        if metric.get('date_start') and metric.get('date_end'):
            # Format dates for display
            try:
                start_date = datetime.strptime(metric['date_start'], '%Y-%m-%d')
                end_date = datetime.strptime(metric['date_end'], '%Y-%m-%d')
                metric['formatted_date_range'] = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
            except:
                metric['formatted_date_range'] = metric['date_range']
    
    return render_template('data.html', metrics=metrics)

@app.route('/export-data')
def export_data():
    """
    Export Fitbit data in the specified format (CSV or JSON).
    
    Query parameters:
    - format: The export format (csv or json)
    """
    export_format = request.args.get('format', 'csv').lower()
    
    if export_format == 'csv':
        # Export as CSV
        csv_data = db.export_data(format='csv')
        
        # Create a response with CSV data
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=fitbit_data.csv'
        
        return response
    elif export_format == 'json':
        # Export as JSON
        json_data = db.export_data(format='json')
        
        # Create a response with JSON data
        response = make_response(json_data)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = 'attachment; filename=fitbit_data.json'
        
        return response
    else:
        return jsonify({"status": "error", "message": f"Unsupported export format: {export_format}"})

@app.route('/delete-metric/<int:metric_id>', methods=['POST'])
def delete_metric(metric_id):
    """
    Delete a specific metric from the database.
    
    Path parameters:
    - metric_id: The ID of the metric to delete
    """
    success = db.delete_metric(metric_id)
    
    if success:
        return jsonify({"status": "success", "message": "Metric deleted successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to delete metric"})

@app.route('/api/metrics')
def api_metrics():
    """
    API endpoint to get all metrics as JSON.
    
    This can be used by frontend JavaScript to update visualizations
    without reloading the page.
    """
    metrics = db.get_all_metrics()
    return jsonify(metrics)

@app.route('/api/add-agent', methods=['POST'])
def add_agent():
    """
    Add a new agent to the system.
    
    This demonstrates how the system can be extended with new agents.
    """
    agent_type = request.form.get('agent_type')
    agent_config = request.json or {}
    
    # In a real implementation, this would dynamically add a new agent to the framework
    
    return jsonify({
        "status": "success", 
        "message": f"Agent of type {agent_type} added (demonstration only)",
        "note": "This is a demonstration endpoint showing how new agents could be added dynamically"
    })

@app.route('/settings')
def settings():
    """Render the settings page for agent configuration."""
    # Here you could load agent configurations from a database or config file
    agent_config = {
        "browser_agent": {"enabled": True},
        "gmail_agent": {"enabled": True},
        "extraction_agent": {"enabled": True},
        "database_agent": {"enabled": True}
    }
    
    return render_template('settings.html', agent_config=agent_config)

@app.route('/update-settings', methods=['POST'])
def update_settings():
    """
    Update agent system settings.
    
    This endpoint handles form submissions from the settings page.
    """
    # Example: update agent configurations
    agent_config = request.form.to_dict()
    
    # Here you could save agent configurations to a database or config file
    
    return redirect(url_for('settings', updated=True))

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
