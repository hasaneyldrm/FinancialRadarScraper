import logging
import time
import traceback
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

logger = logging.getLogger(__name__)

class FinancialScraper:
    """Class to scrape financial data from fintables.com/radar"""
    
    def __init__(self):
        """Initialize the scraper with the target URL"""
        self.url = "https://fintables.com/radar"
        self.timeout = 30  # Timeout in seconds for waiting operations
    
    def setup_driver(self):
        """Set up and configure the Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
            raise
    
    def scrape_data(self):
        """
        Scrape financial data from fintables.com/radar
        
        Returns:
            list: List of dictionaries containing the scraped financial data
        """
        logger.info("Starting data scraping process")
        driver = None
        
        try:
            # Set up the WebDriver
            driver = self.setup_driver()
            
            # Navigate to the target URL
            logger.info(f"Navigating to {self.url}")
            driver.get(self.url)
            
            # Wait for the page to load
            logger.debug("Waiting for page to load")
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give the page some time to fully load JavaScript content
            time.sleep(5)
            
            # Find all radar items - this selector might need adjustment based on the actual site structure
            logger.debug("Extracting radar items")
            items = WebDriverWait(driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".radar-item, .stock-item, .financial-item, .table tr"))
            )
            
            # Extract data from each item
            data = []
            for item in items:
                try:
                    # These selectors need to be adjusted based on the actual structure of the site
                    try:
                        symbol = item.find_element(By.CSS_SELECTOR, ".symbol, .ticker").text
                    except NoSuchElementException:
                        symbol = "N/A"
                    
                    try:
                        name = item.find_element(By.CSS_SELECTOR, ".name, .company-name").text
                    except NoSuchElementException:
                        name = "N/A"
                    
                    try:
                        price = item.find_element(By.CSS_SELECTOR, ".price, .current-price").text
                    except NoSuchElementException:
                        price = "N/A"
                    
                    try:
                        change = item.find_element(By.CSS_SELECTOR, ".change, .price-change").text
                    except NoSuchElementException:
                        change = "N/A"
                    
                    try:
                        volume = item.find_element(By.CSS_SELECTOR, ".volume, .trading-volume").text
                    except NoSuchElementException:
                        volume = "N/A"
                    
                    item_data = {
                        "id": str(uuid.uuid4()),
                        "symbol": symbol,
                        "name": name,
                        "price": price,
                        "change": change,
                        "volume": volume,
                        "timestamp": datetime.now().isoformat()
                    }
                    data.append(item_data)
                except Exception as e:
                    logger.warning(f"Error extracting data from item: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(data)} financial items")
            return data
            
        except TimeoutException:
            logger.error("Timeout while waiting for page elements")
            raise
        except WebDriverException as e:
            logger.error(f"WebDriver error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        finally:
            # Clean up
            if driver:
                try:
                    driver.quit()
                    logger.debug("WebDriver closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing WebDriver: {str(e)}")


    def test_connection(self):
        """Test the connection to the website"""
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(self.url)
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
        finally:
            if driver:
                driver.quit()
