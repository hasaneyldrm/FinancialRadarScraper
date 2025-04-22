import os
import logging
from flask import Flask, jsonify, request, render_template
from data_store import DataStore
from scraper import FinancialScraper
from scheduler import Scheduler

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize data store
data_store = DataStore()

# Initialize scraper
scraper = FinancialScraper()

# Initialize and start the scheduler
scheduler = Scheduler(scraper, data_store)
scheduler.start()

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/data')
def view_data():
    """Render the data visualization page"""
    return render_template('data.html')

@app.route('/api/data', methods=['GET'])
def get_all_data():
    """API endpoint to get all financial data"""
    try:
        all_data = data_store.get_all()
        return jsonify({"status": "success", "data": all_data, "count": len(all_data)})
    except Exception as e:
        logger.error(f"Error retrieving all data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/data/<string:item_id>', methods=['GET'])
def get_data_by_id(item_id):
    """API endpoint to get financial data by ID"""
    try:
        item = data_store.get_by_id(item_id)
        if item:
            return jsonify({"status": "success", "data": item})
        else:
            return jsonify({"status": "error", "message": "Item not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving data by ID: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/force-update', methods=['POST'])
def force_update():
    """API endpoint to force a data update"""
    try:
        scheduler.run_scraper_now()
        return jsonify({"status": "success", "message": "Data update initiated"})
    except Exception as e:
        logger.error(f"Error forcing data update: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """API endpoint to get the status of the scraper and last update time"""
    try:
        status = {
            "last_update": scheduler.last_update_time,
            "is_running": scheduler.is_running,
            "next_update": scheduler.next_update_time,
            "data_count": len(data_store.get_all())
        }
        return jsonify({"status": "success", "data": status})
    except Exception as e:
        logger.error(f"Error retrieving status: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
