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
        
        # Mock alerts and confirmations
        mock_js = """
        window.alert = (msg) => {};
        window.confirm = (msg) => { return true; };
        """
        driver.execute_script(mock_js)
        time.sleep(0.5)
        
        # Click ⬆️ 字 button to open ImportOptionsModal via JS execution
        driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('⬆️ 字') || (b.title && b.title.includes('匯入'))) b.click(); });")
        time.sleep(0.5)
        
        # Verify modal options exist
        page_src = driver.page_source
        assert "📥 選擇匯入來源" in page_src, "ImportOptionsModal header missing"
        assert "載入內建 2000 單字庫" in page_src, "Built-in 2000 option missing"
        assert "載入內建 7000 單字庫" in page_src, "Built-in 7000 option missing"
        assert "從本機選擇檔案 (.txt)" in page_src, "Local TXT option missing"
        
        print("[SUCCESS] test_import_options_modal passed.")
        
    except Exception as e:
        print(f"\n[FAILURE] test_import_options_modal failed, error: {e}", file=sys.stderr)
        try:
            screenshot_path = os.path.join(script_dir, "test_import_modal_failure.png")
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
