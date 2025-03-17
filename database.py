# database.py
import sqlite3
import json
import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database')

class FitbitDatabase:
    def __init__(self, db_path='fitbit_data.db'):
        """
        Initialize the Fitbit database manager.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create the main metrics table
        c.execute('''
        CREATE TABLE IF NOT EXISTS fitbit_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_range TEXT,
            date_start TEXT,
            date_end TEXT,
            step_target_days_met INTEGER,
            best_day_steps INTEGER,
            total_steps INTEGER,
            avg_steps_per_day REAL,
            steps_variance REAL,
            total_miles REAL,
            miles_variance REAL,
            avg_daily_calorie_burn REAL,
            calorie_burn_variance REAL,
            total_active_zone_minutes INTEGER,
            active_zone_minutes_variance INTEGER,
            avg_restful_sleep TEXT,
            restful_sleep_minutes INTEGER,
            restful_sleep_variance INTEGER,
            avg_hours_with_250_steps REAL,
            hours_with_250_steps_variance REAL,
            avg_resting_heart_rate INTEGER,
            resting_heart_rate_variance TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def save_metrics(self, metrics):
        """
        Save Fitbit metrics to the database.
        
        Args:
            metrics (dict): Dictionary containing Fitbit metrics
            
        Returns:
            int: ID of the inserted record or None if failed
        """
        try:
            # Process the metrics to ensure proper data types and formatting
            processed_metrics = self._process_metrics(metrics)
            
            # Check if this date range already exists in the database
            existing_id = self._check_existing_record(processed_metrics.get('date_range'))
            if existing_id:
                # Update existing record
                return self._update_record(existing_id, processed_metrics)
            else:
                # Insert new record
                return self._insert_record(processed_metrics)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return None
    
    def _process_metrics(self, metrics):
        """
        Process and validate metrics before database insertion.
        
        Args:
            metrics (dict): Raw metrics from extraction
            
        Returns:
            dict: Processed metrics ready for database
        """
        processed = {}
        
        # Direct copy of basic fields
        processed['date_range'] = metrics.get('date_range', '')
        
        # Extract start and end dates from the date range
        date_parts = self._parse_date_range(metrics.get('date_range', ''))
        processed['date_start'] = date_parts.get('start_date', '')
        processed['date_end'] = date_parts.get('end_date', '')
        
        # Handle numeric fields with defaults
        processed['step_target_days_met'] = self._safe_int(metrics.get('step_target_days_met')) or 0
        processed['best_day_steps'] = self._safe_int(metrics.get('best_day_steps'))
        processed['total_steps'] = self._safe_int(metrics.get('total_steps'))
        processed['avg_steps_per_day'] = self._safe_float(metrics.get('avg_steps_per_day'))
        processed['total_miles'] = self._safe_float(metrics.get('total_miles'))
        processed['avg_daily_calorie_burn'] = self._safe_float(metrics.get('avg_daily_calorie_burn'))
        processed['total_active_zone_minutes'] = self._safe_int(metrics.get('total_active_zone_minutes'))
        processed['avg_hours_with_250_steps'] = self._safe_float(metrics.get('avg_hours_with_250_steps'))
        processed['avg_resting_heart_rate'] = self._safe_int(metrics.get('avg_resting_heart_rate'))
        
        # Process variance values (may contain text like "▼ 2,693 fewer than last week")
        processed['steps_variance'] = self._process_variance(metrics.get('steps_variance'))
        processed['miles_variance'] = self._process_variance(metrics.get('miles_variance'))
        processed['calorie_burn_variance'] = self._process_variance(metrics.get('calorie_burn_variance'))
        processed['active_zone_minutes_variance'] = self._process_variance(metrics.get('active_zone_minutes_variance'))
        processed['hours_with_250_steps_variance'] = self._process_variance(metrics.get('hours_with_250_steps_variance'))
        
        # Handle special case for heart rate variance (often text like "same as previous week")
        processed['resting_heart_rate_variance'] = metrics.get('resting_heart_rate_variance', '')
        
        # Process sleep data
        processed['avg_restful_sleep'] = metrics.get('avg_restful_sleep', '')
        sleep_minutes = self._parse_sleep_time(metrics.get('avg_restful_sleep', ''))
        processed['restful_sleep_minutes'] = sleep_minutes
        
        # Process sleep variance
        processed['restful_sleep_variance'] = self._process_sleep_variance(metrics.get('restful_sleep_variance', ''))
        
        return processed
    
    def _parse_date_range(self, date_range):
        """
        Parse a date range string into start and end dates.
        
        Args:
            date_range (str): Date range string like "Mar. 3 - Mar. 9"
            
        Returns:
            dict: Dictionary with start_date and end_date
        """
        result = {'start_date': '', 'end_date': ''}
        
        if not date_range:
            return result
        
        # Match pattern like "Mar. 3 - Mar. 9" or "Jan 15 - Jan 21"
        match = re.search(r'([A-Za-z]+\.?\s+\d+)\s*-\s*([A-Za-z]+\.?\s+\d+)', date_range)
        if match:
            start_str, end_str = match.groups()
            
            # Get current year (assume dates are from current year unless we have better info)
            current_year = datetime.now().year
            
            # Parse dates
            try:
                # Handle abbreviations with or without periods
                start_str = start_str.replace('.', '')
                end_str = end_str.replace('.', '')
                
                # Add year
                start_with_year = f"{start_str}, {current_year}"
                end_with_year = f"{end_str}, {current_year}"
                
                # Parse with datetime
                start_date = datetime.strptime(start_with_year, "%b %d, %Y")
                end_date = datetime.strptime(end_with_year, "%b %d, %Y")
                
                # Format as ISO
                result['start_date'] = start_date.strftime("%Y-%m-%d")
                result['end_date'] = end_date.strftime("%Y-%m-%d")
            except Exception as e:
                logger.warning(f"Error parsing date range '{date_range}': {e}")
        
        return result
    
    def _parse_sleep_time(self, sleep_str):
        """
        Parse sleep time string to minutes.
        
        Args:
            sleep_str (str): Sleep time string like "7 hrs 52 min"
            
        Returns:
            int: Total minutes or None if parsing failed
        """
        if not sleep_str:
            return None
        
        try:
            hours = 0
            minutes = 0
            
            # Extract hours
            hour_match = re.search(r'(\d+)\s*hrs?', sleep_str)
            if hour_match:
                hours = int(hour_match.group(1))
            
            # Extract minutes
            min_match = re.search(r'(\d+)\s*min', sleep_str)
            if min_match:
                minutes = int(min_match.group(1))
            
            return hours * 60 + minutes
        except Exception:
            return None
    
    def _process_variance(self, variance_str):
        """
        Process variance strings to extract numerical values with direction.
        
        Args:
            variance_str (str): Variance string like "▼ 2,693 fewer than last week"
            
        Returns:
            float: Numerical variance (negative for decreases, positive for increases)
        """
        if not variance_str:
            return 0
        
        # If already a number, return it
        if isinstance(variance_str, (int, float)):
            return float(variance_str)
        
        try:
            # Handle "same as previous week" or similar
            if isinstance(variance_str, str) and ("same" in variance_str.lower()):
                return 0
            
            # Extract numeric part and determine direction
            is_negative = any(marker in variance_str for marker in ["▼", "fewer", "below", "lower", "less", "-"])
            is_positive = any(marker in variance_str for marker in ["▲", "more", "above", "higher", "extra", "+"])
            
            # Find numbers in the string
            numbers = re.findall(r"[-+]?\d+\.?\d*", variance_str.replace(",", ""))
            if numbers:
                value = float(numbers[0])
                return -value if is_negative else (value if is_positive else value)
            
            return 0
        except Exception as e:
            logger.warning(f"Error processing variance '{variance_str}': {e}")
            return 0
    
    def _process_sleep_variance(self, variance_str):
        """
        Process sleep variance strings to extract minutes.
        
        Args:
            variance_str (str): Variance string like "▼ 0 hrs 23 min lower than last week"
            
        Returns:
            int: Minutes of variance (negative for decreases, positive for increases)
        """
        if not variance_str:
            return 0
        
        try:
            # Handle "same as previous week" or similar
            if "same" in variance_str.lower():
                return 0
            
            # Determine direction
            is_negative = any(marker in variance_str for marker in ["▼", "fewer", "below", "lower", "less", "-"])
            
            # Extract hours and minutes
            hours = 0
            minutes = 0
            
            hour_match = re.search(r'(\d+)\s*hrs?', variance_str)
            if hour_match:
                hours = int(hour_match.group(1))
            
            min_match = re.search(r'(\d+)\s*min', variance_str)
            if min_match:
                minutes = int(min_match.group(1))
            
            total_minutes = hours * 60 + minutes
            return -total_minutes if is_negative else total_minutes
        except Exception as e:
            logger.warning(f"Error processing sleep variance '{variance_str}': {e}")
            return 0
    
    def _check_existing_record(self, date_range):
        """
        Check if a record with the given date range already exists.
        
        Args:
            date_range (str): Date range to check
            
        Returns:
            int: ID of existing record or None if not found
        """
        if not date_range:
            return None
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM fitbit_metrics WHERE date_range = ?", (date_range,))
        result = c.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def _insert_record(self, metrics):
        """
        Insert a new record into the database.
        
        Args:
            metrics (dict): Processed metrics
            
        Returns:
            int: ID of the inserted record
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        INSERT INTO fitbit_metrics (
            date_range,
            date_start,
            date_end,
            step_target_days_met,
            best_day_steps,
            total_steps,
            avg_steps_per_day,
            steps_variance,
            total_miles,
            miles_variance,
            avg_daily_calorie_burn,
            calorie_burn_variance,
            total_active_zone_minutes,
            active_zone_minutes_variance,
            avg_restful_sleep,
            restful_sleep_minutes,
            restful_sleep_variance,
            avg_hours_with_250_steps,
            hours_with_250_steps_variance,
            avg_resting_heart_rate,
            resting_heart_rate_variance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.get('date_range'),
            metrics.get('date_start'),
            metrics.get('date_end'),
            metrics.get('step_target_days_met'),
            metrics.get('best_day_steps'),
            metrics.get('total_steps'),
            metrics.get('avg_steps_per_day'),
            metrics.get('steps_variance'),
            metrics.get('total_miles'),
            metrics.get('miles_variance'),
            metrics.get('avg_daily_calorie_burn'),
            metrics.get('calorie_burn_variance'),
            metrics.get('total_active_zone_minutes'),
            metrics.get('active_zone_minutes_variance'),
            metrics.get('avg_restful_sleep'),
            metrics.get('restful_sleep_minutes'),
            metrics.get('restful_sleep_variance'),
            metrics.get('avg_hours_with_250_steps'),
            metrics.get('hours_with_250_steps_variance'),
            metrics.get('avg_resting_heart_rate'),
            metrics.get('resting_heart_rate_variance')
        ))
        
        last_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return last_id
    
    def _update_record(self, record_id, metrics):
        """
        Update an existing record in the database.
        
        Args:
            record_id (int): ID of the record to update
            metrics (dict): Processed metrics
            
        Returns:
            int: ID of the updated record
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        UPDATE fitbit_metrics SET
            date_start = ?,
            date_end = ?,
            step_target_days_met = ?,
            best_day_steps = ?,
            total_steps = ?,
            avg_steps_per_day = ?,
            steps_variance = ?,
            total_miles = ?,
            miles_variance = ?,
            avg_daily_calorie_burn = ?,
            calorie_burn_variance = ?,
            total_active_zone_minutes = ?,
            active_zone_minutes_variance = ?,
            avg_restful_sleep = ?,
            restful_sleep_minutes = ?,
            restful_sleep_variance = ?,
            avg_hours_with_250_steps = ?,
            hours_with_250_steps_variance = ?,
            avg_resting_heart_rate = ?,
            resting_heart_rate_variance = ?
        WHERE id = ?
        ''', (
            metrics.get('date_start'),
            metrics.get('date_end'),
            metrics.get('step_target_days_met'),
            metrics.get('best_day_steps'),
            metrics.get('total_steps'),
            metrics.get('avg_steps_per_day'),
            metrics.get('steps_variance'),
            metrics.get('total_miles'),
            metrics.get('miles_variance'),
            metrics.get('avg_daily_calorie_burn'),
            metrics.get('calorie_burn_variance'),
            metrics.get('total_active_zone_minutes'),
            metrics.get('active_zone_minutes_variance'),
            metrics.get('avg_restful_sleep'),
            metrics.get('restful_sleep_minutes'),
            metrics.get('restful_sleep_variance'),
            metrics.get('avg_hours_with_250_steps'),
            metrics.get('hours_with_250_steps_variance'),
            metrics.get('avg_resting_heart_rate'),
            metrics.get('resting_heart_rate_variance'),
            record_id
        ))
        
        conn.commit()
        conn.close()
        
        return record_id
    
    def _safe_int(self, value):
        """
        Safely convert a value to integer, returning None if conversion fails.
        
        Args:
            value: Value to convert
            
        Returns:
            int or None: Converted value or None if conversion failed
        """
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Remove commas and other non-numeric characters
                clean_value = re.sub(r'[^\d.-]', '', value)
                return int(float(clean_value)) if clean_value else None
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value):
        """
        Safely convert a value to float, returning None if conversion fails.
        
        Args:
            value: Value to convert
            
        Returns:
            float or None: Converted value or None if conversion failed
        """
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Remove commas and other non-numeric characters
                clean_value = re.sub(r'[^\d.-]', '', value)
                return float(clean_value) if clean_value else None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_all_metrics(self):
        """
        Get all metrics from the database, ordered by date.
        
        Returns:
            list: List of dictionaries containing all metrics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
        SELECT * FROM fitbit_metrics 
        ORDER BY date_start DESC, date_end DESC
        ''')
        
        results = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return results
    
    def get_metrics_by_date_range(self, start_date, end_date):
        """
        Get metrics for a specific date range.
        
        Args:
            start_date (str): Start date in ISO format (YYYY-MM-DD)
            end_date (str): End date in ISO format (YYYY-MM-DD)
            
        Returns:
            list: List of dictionaries containing metrics in the date range
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
        SELECT * FROM fitbit_metrics 
        WHERE date_start >= ? AND date_end <= ?
        ORDER BY date_start, date_end
        ''', (start_date, end_date))
        
        results = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return results
    
    def export_data(self, format='json'):
        """
        Export all data in the specified format.
        
        Args:
            format (str): Export format ('json' or 'csv')
            
        Returns:
            str: Data in the requested format
        """
        data = self.get_all_metrics()
        
        if format.lower() == 'json':
            return json.dumps(data, indent=2)
        elif format.lower() == 'csv':
            if not data:
                return "No data available"
            
            # Create CSV string
            headers = data[0].keys()
            csv_rows = [",".join(headers)]
            
            for item in data:
                row = []
                for key in headers:
                    # Handle None values and convert to string
                    value = item.get(key, "")
                    if value is None:
                        value = ""
                    # Escape commas in values
                    if isinstance(value, str) and "," in value:
                        value = f'"{value}"'
                    row.append(str(value))
                csv_rows.append(",".join(row))
            
            return "\n".join(csv_rows)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def delete_metric(self, metric_id):
        """
        Delete a metric from the database.
        
        Args:
            metric_id (int): ID of the metric to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("DELETE FROM fitbit_metrics WHERE id = ?", (metric_id,))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting metric {metric_id}: {e}")
            return False