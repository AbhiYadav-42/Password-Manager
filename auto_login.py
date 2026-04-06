from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import undetected_chromedriver as uc
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

  brave_version = None
  driver_path = None
  
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
  
  # Use undetected-chromedriver wrapper to bypass bot detection
  try:
    if brave_version and driver_path:
      driver = uc.Chrome(driver_executable_path=driver_path, options=options, version_main=int(brave_version))
    else:
      driver = uc.Chrome(options=options)
  except:
    print("Warning: undetected-chromedriver failed, falling back to standard Selenium")
    driver = webdriver.Chrome(options=options)

  try:
    # Validate and normalize URL
    if not url.startswith(('http://', 'https://')):
      url = 'https://' + url
    
    print(f"Navigating to: {url}")
    driver.get(url)
    
    # Wait for JavaScript to be ready before looking for elements
    print("Waiting for page JavaScript to load...")
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    print("✓ Page loaded successfully")
    
    wait = WebDriverWait(driver, 15)

    # Find and fill email/username field - try multiple selectors with shorter timeouts
    user_field = None
    email_selectors = [
        (By.CSS_SELECTOR, "input#identifierId"),  # Google - try this FIRST
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[name='username']"),
        (By.CSS_SELECTOR, "input[aria-label*='email']"),
        (By.CSS_SELECTOR, "input[placeholder*='email']"),
        (By.CSS_SELECTOR, "input[placeholder*='username']"),
    ]
    
    for selector in email_selectors:
      try:
        # Use shorter timeout (3 sec) and clickable wait (faster than presence)
        user_field = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(selector))
        print(f"✓ Found email/username field with selector: {selector}")
        break
      except:
        continue
    
    if user_field is None:
      raise Exception("Could not find email or username field")
    
    user_field.clear()
    user_field.send_keys(username)
    print(f"✓ Entered username: {username}")

    # Detect single vs multi-page login
    try:
      # Try to find password field immediately (single-page) with shorter timeouts
      pass_field = None
      password_selectors = [
          (By.CSS_SELECTOR, "input#password"),  # Google password field
          (By.CSS_SELECTOR, "input#Passwd"),  # Older Google
          (By.CSS_SELECTOR, "input[name='password']"),
          (By.CSS_SELECTOR, "input[type='password']"),
          (By.CSS_SELECTOR, "input[name='pass']"),
      ]
      
      for selector in password_selectors:
        try:
          # Use shorter timeout (2 sec) and clickable wait
          pass_field = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(selector))
          print(f"✓ Found password field with selector: {selector}")
          print("Detected: Single-page login")
          break
        except:
          continue
      
      if pass_field is None:
        raise Exception()
      
      pass_field.send_keys(password)
      print(f"✓ Entered password")

    except:
      # Multi-page login: password appears after clicking next
      print("Detected: Multi-page login")
      next_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
      print("Clicking next button...")
      next_btn.click()
      
      # Wait for password field to appear on next page
      print("Waiting for password page to load...")
      WebDriverWait(driver, 10).until(
          lambda d: d.execute_script("return document.readyState") == "complete"
      )
      
      # Wait for password field to appear on next page - try multiple selectors
      pass_field = None
      password_selectors = [
          (By.CSS_SELECTOR, "input#password"),
          (By.CSS_SELECTOR, "input#Passwd"),
          (By.CSS_SELECTOR, "input[name='password']"),
          (By.CSS_SELECTOR, "input[type='password']"),
          (By.CSS_SELECTOR, "input[name='pass']"),
      ]
      
      for selector in password_selectors:
        try:
          pass_field = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(selector))
          print(f"✓ Found password field with selector: {selector}")
          break
        except:
          continue
      
      if pass_field is None:
        raise Exception("Could not find password field on next page")
      
      print("Found password field on next page")
      pass_field.send_keys(password)
      print(f"✓ Entered password")

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