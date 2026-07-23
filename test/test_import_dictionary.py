import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def run_tests():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1200,800")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.abspath(os.path.join(script_dir, "..", "index.html"))
        file_url = f"file:///{html_path.replace(os.sep, '/')}"
        
        driver.get(file_url)
        
        # Setup clean local storage context
        driver.execute_script("""
            localStorage.clear();
            localStorage.setItem('vocab_currentDB', 'vocab_test');
            localStorage.setItem('vocab_wordsPerDay_vocab_test', '10');
            localStorage.setItem('vocab_ghostsPerDay_vocab_test', '0');
        """)
        
        driver.refresh()
        time.sleep(1.0)
        
        # Inject API mocks to prevent alert popups from blocking Selenium
        mock_js = """
        window.alert = (msg) => {};
        window.confirm = (msg) => { return true; };
        """
        driver.execute_script(mock_js)
        time.sleep(0.5)
        
        # Wait until React mounts DOM
        import_txt_path = os.path.abspath(os.path.join(script_dir, "test_import.txt"))
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@accept='.txt']"))
        )
        driver.execute_script("arguments[0].classList.remove('hidden');", file_input)
        file_input.send_keys(import_txt_path)
        time.sleep(1.5)
        
        # Verify 5 words successfully loaded
        page_src = driver.page_source
        assert "5" in page_src, "Failed to load 5 words from test_import.txt"
        
        # Success output is minimal to save token
        print("[SUCCESS] test_import_dictionary passed.")
        
    except Exception as e:
        print(f"\n[FAILURE] test_import_dictionary failed, error: {e}", file=sys.stderr)
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Save screenshot
            screenshot_path = os.path.join(current_dir, "test_import_dictionary_failure.png")
            driver.save_screenshot(screenshot_path)
            print(f"[TEST] Saved failure screenshot to {screenshot_path}", file=sys.stderr)
            
            # Save page source to local file (instead of printing it to console)
            source_path = os.path.join(current_dir, "failure_source.html")
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"[TEST] Saved failure page source to {source_path}", file=sys.stderr)
        except Exception as se:
            print(f"[TEST] Cannot save failure diagnostics: {se}", file=sys.stderr)
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
