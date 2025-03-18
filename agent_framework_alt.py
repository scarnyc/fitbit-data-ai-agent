# Run the agent graph
        try:
            logger.info(f"Starting Fitbit agent system with start date {start_date}")
            final_state = self.graph.invoke(initial_state)

            # Safely extract values from any state object type
            def safe_get(obj, key, default=None):
                try:
                    if hasattr(obj, 'get') and callable(obj.get):
                        return obj.get(key, default)
                    elif hasattr(obj, key):
                        return getattr(obj, key, default)
                    elif hasattr(obj, '__getitem__'):
                        return obj[key] if key in obj else default
                    return default
                except:
                    return default

            # Get status and log completion
            status = safe_get(final_state, 'status', 'unknown')
            logger.info(f"Agent system completed with status: {status}")

            # Convert to consistent result format
            result = {
                "status": status,
                "summary": safe_get(final_state, 'summary', ''),
                "error": safe_get(final_state, 'error', ''),
                "extracted_data": safe_get(final_state, 'extracted_data', []),
                "saved_records": safe_get(final_state, 'saved_records', [])
            }
except Exception as e:
            logger.error(f"Agent system error: {e}")
            result = {
                "status": "error",
                "summary": "Agent system encountered an error",
                "error": str(e),
                "extracted_data": [],
                "saved_records": []
            }

        return result