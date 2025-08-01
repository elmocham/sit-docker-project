import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# The URL will be http://localhost because the test runs in the same network as the docker-compose services
APP_URL = "http://localhost:80" 
# Correct credentials
USERNAME = "student"
PASSWORD = "2301769"

def run_test():
    print("Setting up Chrome options for headless mode...")
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Run without a visible browser window
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Navigating to {APP_URL}")
        driver.get(APP_URL)
        time.sleep(2) # Wait for page to load

        print("Finding login form elements...")
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.TAG_NAME, "button").click()
        
        print("Login button clicked. Waiting for dashboard...")
        time.sleep(3) # Wait for redirect and page load

        print(f"Current URL: {driver.current_url}")
        assert "/dashboard" in driver.current_url

        print("Checking for welcome message on dashboard...")
        page_source = driver.page_source
        assert "Welcome, student!" in page_source
        assert "Your unique session ID is:" in page_source
        
        print("UI Test Passed!")

    except Exception as e:
        print(f"UI Test Failed: {e}")
        # Save a screenshot for debugging in GitHub Actions artifacts
        driver.save_screenshot("test_failure_screenshot.png")
        raise # Re-raise the exception to make the test fail
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_test()