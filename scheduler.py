import logging
import threading
import time
import schedule
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Scheduler:
    """Class to schedule and manage the periodic scraping of financial data"""
    
    def __init__(self, scraper, data_store, interval_minutes=60):
        """
        Initialize the scheduler with the given scraper and data store
        
        Args:
            scraper: Instance of the financial data scraper
            data_store: Instance of the data store
            interval_minutes (int): Interval in minutes between scraping runs
        """
        self.scraper = scraper
        self.data_store = data_store
        self.interval_minutes = interval_minutes
        self.is_running = False
        self.last_update_time = None
        self.next_update_time = None
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        
        logger.info(f"Scheduler initialized with {interval_minutes} minute interval")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # Run the scraper immediately on startup
        self.run_scraper_now()
        
        # Schedule regular scraping
        schedule.every(self.interval_minutes).minutes.do(self.run_scraper)
        self.next_update_time = datetime.now() + timedelta(minutes=self.interval_minutes)
        
        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler not running")
            return
        
        self.stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Internal method that runs the scheduler loop"""
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    
    def run_scraper(self):
        """Run the scraper and update the data store"""
        try:
            logger.info("Running scheduled scraping task")
            data = self.scraper.scrape_data()
            self.data_store.update_data(data)
            self.last_update_time = datetime.now()
            self.next_update_time = datetime.now() + timedelta(minutes=self.interval_minutes)
            logger.info(f"Scheduled scraping completed successfully, next update at {self.next_update_time}")
            return True
        except Exception as e:
            logger.error(f"Error during scheduled scraping: {str(e)}")
            # Even on error, update the next scheduled time
            self.next_update_time = datetime.now() + timedelta(minutes=self.interval_minutes)
            return False
    
    def run_scraper_now(self):
        """Manually trigger the scraper to run immediately"""
        threading.Thread(target=self.run_scraper, daemon=True).start()
        logger.info("Manual scraping task initiated")
