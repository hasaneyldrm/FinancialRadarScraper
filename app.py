import os
import logging
from flask import Flask, jsonify, request, render_template
from data_store import DataStore
from scraper import FinancialScraper
from scheduler import Scheduler
from flask_swagger_ui import get_swaggerui_blueprint

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Financial Data API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

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
        # Create a simplified format as requested
        simplified_data = []
        for item in all_data:
            simplified_item = {
                "name": item.get("name", ""),  # Using the full company name
                "price": item.get("price", "")
                # Icon is optional and not included in current data structure
            }
            simplified_data.append(simplified_item)
        
        # Return both the simplified and full data formats
        return jsonify({
            "status": "success", 
            "data": simplified_data,  # Simplified format as requested
            "full_data": all_data,    # Original full data
            "count": len(all_data)
        })
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

@app.route('/api/stock/<string:name>', methods=['GET'])
def get_data_by_name(name):
    """API endpoint to get financial data by name/symbol"""
    try:
        item = data_store.get_by_name(name)
        if item:
            return jsonify({"status": "success", "data": item})
        else:
            return jsonify({"status": "error", "message": f"Stock with name/symbol '{name}' not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving data by name: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/getDataByName/<string:name>', methods=['GET'])
def get_data_by_name_explicit(name):
    """Explicit API endpoint to get financial data by name/symbol"""
    try:
        item = data_store.get_by_name(name)
        if item:
            return jsonify({"status": "success", "data": item})
        else:
            return jsonify({"status": "error", "message": f"Stock with name/symbol '{name}' not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving data by name: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
        
@app.route('/api/getBulkDataByNames', methods=['GET'])
def get_bulk_data_by_names_get():
    """API endpoint to get multiple financial data items by comma-separated names/symbols"""
    try:
        # Get the comma-separated list of names from the 'names' query parameter
        names_param = request.args.get('names', '')
        if not names_param:
            return jsonify({"status": "error", "message": "No names provided. Use 'names' query parameter with comma-separated values"}), 400
            
        # Split the names by comma and strip whitespace
        names = [name.strip() for name in names_param.split(',')]
        
        # Get data for each name
        results = []
        for name in names:
            item = data_store.get_by_name(name)
            if item:
                results.append(item)
        
        # Return results even if some names weren't found
        return jsonify({
            "status": "success", 
            "data": results,
            "count": len(results),
            "requested": len(names),
            "missing": len(names) - len(results)
        })
    except Exception as e:
        logger.error(f"Error retrieving bulk data by names: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/getBulkDataByNames', methods=['POST'])
def get_bulk_data_by_names_post():
    """API endpoint to get multiple stocks data by names/symbols"""
    try:
        names = request.json.get('symbols', [])
        if not names:
            return jsonify({"status": "error", "message": "No symbols provided"}), 400
            
        results = []
        for name in names:
            item = data_store.get_by_name(name)
            if item:
                results.append({
                    "symbol": item.get("symbol"),
                    "name": item.get("name"),
                    "price": item.get("price")
                })
                
        return jsonify({
            "status": "success",
            "data": results,
            "count": len(results)
        })
    except Exception as e:
        logger.error(f"Error retrieving bulk data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/force-update', methods=['POST', 'GET'])
def force_update():
    """API endpoint to force a data update"""
    try:
        # Run the scraper directly for immediate results
        data = scraper.scrape_data()
        data_store.update_data(data)
        return jsonify({
            "status": "success", 
            "message": "Data update completed", 
            "count": len(data)
        })
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
    app.run(host='0.0.0.0', port=5000)
