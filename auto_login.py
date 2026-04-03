from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time
import subprocess

def auto_login_brave(url, username, password):
  
  options = Options()
  #path to brave
  options.binary_location='/usr/bin/brave-browser'
  options.add_argument("--disable-extensions")
  options.add_argument("--disable-notifications")
  options.add_argument("--disable-infobars")
  options.add_argument("--disable-background-networking")
  options.add_argument("--disable-sync")

  try:
    # Get Brave browser version
    result = subprocess.run(['/usr/bin/brave-browser', '--version'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
# Extract version string, e.g., "Brave Browser 145.0.7632.109" -> "145"
      version_parts = result.stdout.strip().split()

      if len(version_parts) >= 3:
        brave_version = version_parts[2].split('.')[0]  # Get major version only
        print(f"Detected Brave version: {brave_version}")
        driver_path = ChromeDriverManager(
          driver_version="145.0.7632.109",
          chrome_type=ChromeType.BRAVE).install()

      else:
        print("Could not parse Brave version, using latest ChromeDriver")
        driver_path = ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()

    else:
      print("Could not detect Brave version, using latest ChromeDriver")
      driver_path = ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()

  except Exception as e:
    print(f"Warning: Could not auto-detect driver version: {e}")
    print("Falling back to latest ChromeDriver")
    driver_path = ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()
  
  service = Service(driver_path)
  driver = webdriver.Chrome(service=service, options=options)

  try:
    # Validate and normalize URL
    if not url.startswith(('http://', 'https://')):
      url = 'https://' + url
    
    print(f"Navigating to: {url}")
    driver.get(url)
    
    wait = WebDriverWait(driver, 15)

    # Find and fill email field
    user_field = wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, "input[name='email']"
    )))
    user_field.clear()
    user_field.send_keys(username)

    # Detect single vs multi-page login
    try:
      # Try to find password field immediately (single-page)
      pass_field = WebDriverWait(driver, 2).until(EC.presence_of_element_located((
          By.CSS_SELECTOR, "input[name='pass']"
      )))
      print("Detected: Single-page login")
      pass_field.send_keys(password)

    except:
      # Multi-page login: password appears after clicking next
      print("Detected: Multi-page login")
      next_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
      print("Clicking next button...")
      next_btn.click()
      
      # Wait for password field to appear on next page
      pass_field = wait.until(EC.presence_of_element_located((
          By.CSS_SELECTOR, "input[name='pass']"
      )))
      print("Found password field on next page")
      pass_field.send_keys(password)

    # Find and click login button
    login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
    print("Clicking login button...")
    login_button.click()

    print("Login sequence completed.")
    # Wait for page to load to verify successful login
    WebDriverWait(driver, 10).until(EC.url_changes(url))
    driver.quit()

  except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
    try:
      driver.quit()
    except:
      pass