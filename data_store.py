import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class DataStore:
    """Class to store and manage the scraped financial data"""
    
    def __init__(self):
        """Initialize the data store"""
        self.data = []
        self.lock = threading.Lock()
        self.last_update = None
        logger.info("Data store initialized")
    
    def update_data(self, new_data):
        """
        Update the stored data with newly scraped data
        
        Args:
            new_data (list): List of dictionaries containing the scraped financial data
        """
        if not new_data:
            logger.warning("Attempted to update with empty data, ignoring")
            return
        
        with self.lock:
            self.data = new_data
            self.last_update = datetime.now()
            logger.info(f"Data store updated with {len(new_data)} items at {self.last_update}")
    
    def get_all(self):
        """
        Get all stored financial data
        
        Returns:
            list: List of dictionaries containing all financial data
        """
        with self.lock:
            return self.data.copy()
    
    def get_by_id(self, item_id):
        """
        Get a specific financial data item by ID
        
        Args:
            item_id (str): ID of the item to retrieve
            
        Returns:
            dict: Dictionary containing the financial data item, or None if not found
        """
        with self.lock:
            for item in self.data:
                if item.get('id') == item_id:
                    return item
            return None
    
    def get_last_update_time(self):
        """
        Get the timestamp of the last data update
        
        Returns:
            datetime: Timestamp of the last update, or None if no updates have occurred
        """
        with self.lock:
            return self.last_update
    
    def clear(self):
        """Clear all stored data"""
        with self.lock:
            self.data = []
            logger.info("Data store cleared")
