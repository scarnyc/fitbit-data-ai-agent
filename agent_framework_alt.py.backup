        # Run the agent graph
        try:
            logger.info(f"Starting Fitbit agent system with start date {start_date}")
            final_state = self.graph.invoke(initial_state)
            
            # Handle different return types from graph.invoke
            # It might return a dict-like object or the AgentState object directly
            if hasattr(final_state, 'get') and callable(final_state.get):
                # Dict-like object
                status = final_state.get('status', 'unknown')
                logger.info(f"Agent system completed with status: {status}")
                
                # Convert to dict for return
                result = {
                    "status": status,
                    "summary": final_state.get('summary', ''),
                    "error": final_state.get('error', ''),
                    "extracted_data": final_state.get('extracted_data', []),
                    "saved_records": final_state.get('saved_records', [])
                }
            elif isinstance(final_state, AgentState):
                # AgentState object
                logger.info(f"Agent system completed with status: {final_state.status}")
                
                # Convert dataclass to dict for return
                result = {
                    "status": final_state.status,
                    "summary": final_state.summary,
                    "error": final_state.error,
                    "extracted_data": final_state.extracted_data,
                    "saved_records": final_state.saved_records
                }
            else:
                # Unknown type, create a generic result
                logger.warning(f"Unknown final state type: {type(final_state)}")
                result = {
                    "status": "unknown",
                    "summary": "Process completed with unknown state",
                    "error": f"Unexpected return type: {type(final_state)}",
                    "extracted_data": [],
                    "saved_records": []
                }