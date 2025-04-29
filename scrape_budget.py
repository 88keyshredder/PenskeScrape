from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import json
import os
import time
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get arguments (could be passed from the GitHub Action)
location = sys.argv[1] if len(sys.argv) > 1 else "Tempe, AZ"
pickup_date = sys.argv[2] if len(sys.argv) > 2 else "04/30/2025"
dropoff_date = sys.argv[3] if len(sys.argv) > 3 else "04/30/2025" 
output_path = sys.argv[4] if len(sys.argv) > 4 else "penske_data.csv"

# Configure Chrome for GitHub Actions environment
chrome_options = Options()
options = [
    "--headless",
    "--disable-gpu",
    "--window-size=1920,1200",
    "--ignore-certificate-errors",
    "--disable-extensions",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-notifications",
    "--disable-geolocation"
]
for option in options:
    chrome_options.add_argument(option)

# Initialize the WebDriver
service = Service(ChromeDriverManager().install())

def scrape_penske_availability():
    logger.info("Starting Penske scraper...")
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 20)
        logger.info("Web driver initialized")
        
        # Navigate to Penske website
        driver.get("https://www.pensketruckrental.com/")
        logger.info("Loaded Penske website")
        
        # Wait for the page to load fully
        time.sleep(3)
        
        # Handle any location permission dialogs by dismissing them
        try:
            driver.execute_script("navigator.geolocation.clearWatch = function() {};")
            driver.execute_script("navigator.geolocation.getCurrentPosition = function() {};")
            logger.info("Disabled geolocation prompts")
        except Exception as e:
            logger.warning(f"Could not disable geolocation: {e}")
        
        # Find and click the return location dropdown
        try:
            return_location_dropdown = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "fieldset.quote-fieldset-selector div.quote-select"))
            )
            return_location_dropdown.click()
            logger.info("Clicked return location dropdown")
            
            # Select 'Same Location' option
            same_location_option = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "span.quote-option[data-value='same-location']"))
            )
            same_location_option.click()
            logger.info("Selected 'Same Location' option")
        except Exception as e:
            logger.error(f"Error selecting return location: {e}")
        
        # Enter pickup location
        try:
            pickup_input = wait.until(
                EC.element_to_be_clickable((By.ID, "pickup_location_txtboxHM"))
            )
            pickup_input.clear()
            pickup_input.send_keys(location)
            time.sleep(1)
            pickup_input.send_keys(Keys.ENTER)
            logger.info(f"Entered pickup location: {location}")
            time.sleep(2)  # Wait for location to be processed
        except Exception as e:
            logger.error(f"Error entering pickup location: {e}")
        
        # Click on the date input to open the calendar
        try:
            date_input = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[formcontrolname='tripDates']"))
            )
            date_input.click()
            logger.info("Clicked on date input")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error clicking on date input: {e}")
        
        # Select pickup date from the calendar
        try:
            # For this example, we'll click on a specific date (e.g., the 30th of April)
            # Find all date elements and click on the one with text "30"
            pickup_date_element = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//date//div[contains(@class, 'grid-block-normal')]//span[text()='30']"))
            )
            pickup_date_element.click()
            logger.info("Selected pickup date")
            time.sleep(1)
            
            # For this example, we'll click on the same date for dropoff
            dropoff_date_element = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//date//div[contains(@class, 'grid-block-normal')]//span[text()='30']"))
            )
            dropoff_date_element.click()
            logger.info("Selected dropoff date")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error selecting dates: {e}")
        
        # Click continue button on the calendar
        try:
            continue_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'mdc-button__label') and text()='Continue']"))
            )
            continue_button.click()
            logger.info("Clicked continue button on calendar")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error clicking continue button: {e}")
        
        # Click search button
        try:
            search_button = wait.until(
                EC.element_to_be_clickable((By.ID, "submitbuttonHM"))
            )
            search_button.click()
            logger.info("Clicked search button")
            
            # Wait for results page to load
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error clicking search button: {e}")
        
        # Scrape available truck options
        trucks_data = []
        try:
            # Wait for the results to load
            truck_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.truck-option"))
            )
            
            # Extract data for each truck option
            for truck in truck_elements:
                try:
                    truck_type = truck.find_element(By.CSS_SELECTOR, "h3.truck-title").text
                    price = truck.find_element(By.CSS_SELECTOR, "div.price-value").text
                    
                    # Additional details if available
                    details = {}
                    try:
                        details_elements = truck.find_elements(By.CSS_SELECTOR, "div.truck-details li")
                        for detail in details_elements:
                            detail_text = detail.text
                            if ":" in detail_text:
                                key, value = detail_text.split(":", 1)
                                details[key.strip()] = value.strip()
                    except Exception:
                        pass
                        
                    trucks_data.append({
                        "truck_type": truck_type,
                        "price": price,
                        "details": details
                    })
                except Exception as e:
                    logger.warning(f"Error extracting truck data: {e}")
            
            logger.info(f"Scraped {len(trucks_data)} truck options")
        except Exception as e:
            logger.error(f"Error scraping truck options: {e}")
        
        # Create DataFrame and save to CSV
        if trucks_data:
            # Save raw data as JSON
            with open(output_path.replace('.csv', '.json'), 'w') as f:
                json.dump(trucks_data, f, indent=2)
            
            # Create and save CSV
            df = pd.json_normalize(trucks_data)
            df.to_csv(output_path, index=False)
            logger.info(f"Data saved to {output_path}")
        else:
            logger.warning("No truck data found")
        
        return trucks_data
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
    
    finally:
        try:
            driver.quit()
            logger.info("Driver closed")
        except Exception:
            pass

if __name__ == "__main__":
    result = scrape_penske_availability()
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Failed to scrape data")
