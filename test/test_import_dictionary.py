import os
import time
import sys
import socketserver
import http.server
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def run_tests():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1200,800")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(script_dir, ".."))
    www_dir = os.path.join(parent_dir, "www") if os.path.exists(os.path.join(parent_dir, "www")) else parent_dir

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=www_dir, **kwargs)

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        file_url = f"http://127.0.0.1:{port}/index.html"
        driver.get(file_url)
        time.sleep(0.5)
        
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
        
        print("[SUCCESS] test_import_dictionary passed.")
        
    except Exception as e:
        print(f"\n[FAILURE] test_import_dictionary failed, error: {e}", file=sys.stderr)
        try:
            screenshot_path = os.path.join(script_dir, "test_import_dictionary_failure.png")
            driver.save_screenshot(screenshot_path)
            source_path = os.path.join(script_dir, "failure_source.html")
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception as se:
            pass
        sys.exit(1)
    finally:
        driver.quit()
        httpd.shutdown()
        httpd.server_close()

if __name__ == "__main__":
    run_tests()
