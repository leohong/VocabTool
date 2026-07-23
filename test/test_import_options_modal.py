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
            current_dir = os.path.dirname(os.path.abspath(__file__))
            screenshot_path = os.path.join(current_dir, "test_import_modal_failure.png")
            driver.save_screenshot(screenshot_path)
            source_path = os.path.join(current_dir, "failure_source.html")
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception as se:
            pass
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
