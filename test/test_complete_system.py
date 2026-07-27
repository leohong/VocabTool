import time
import os
import sys
import json
import socket
import http.server
import socketserver
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRECTORY = os.path.abspath(os.path.join(BASE_DIR, "..", "www"))
httpd = None
PORT = None

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

# 1. Setup local HTTP server on a dynamically assigned free port on 127.0.0.1
print("[Main] Starting web server on a dynamic free port...")
socketserver.TCPServer.allow_reuse_address = True
try:
    httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    PORT = httpd.server_address[1]
    print(f"[Main] Web server successfully started on port {PORT}. Serving files from '{DIRECTORY}'...")
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(1) # Give server a moment to spin up
except Exception as e:
    print(f"[Main] Error starting server: {e}")
    sys.exit(1)

# 2. Setup screenshots directory
screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(screenshot_dir, exist_ok=True)
print(f"[Main] Screenshots will be saved to: {screenshot_dir}")

# 3. Setup WebDriver
print("[Main] Configuring Chrome WebDriver...")
try:
    import chromedriver_autoinstaller
    print("[Main] Running chromedriver_autoinstaller...")
    chromedriver_autoinstaller.install()
except Exception as e:
    print(f"[Main] Warning: chromedriver_autoinstaller failed ({e}). Falling back to Selenium Manager.")

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1280,1024')
options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.cookies": 1
})

driver = webdriver.Chrome(options=options)
# Set page load timeout to avoid hanging indefinitely
driver.set_page_load_timeout(15)
wait = WebDriverWait(driver, 8)

try:
    # URL to load
    target_url = f"http://127.0.0.1:{PORT}/index.html"
    print(f"[Main] Navigating to {target_url}...")
    driver.get(target_url)
    time.sleep(2)

    # --- STEP 1: INITIALIZE MOCK DATA ---
    print("[Step 1] Initializing localStorage with mock database...")
    driver.execute_script("""
        localStorage.clear();
        localStorage.setItem('vocab_currentDB', 'vocab_system_test');
        localStorage.setItem('vocab_dbList', JSON.stringify(['vocab_system_test']));
        localStorage.setItem('vocab_customVocab_vocab_system_test', JSON.stringify([
            { en: "acknowledge", zh: "確認", pos: "v.", eg: "Please acknowledge receipt of this email." },
            { en: "abandon", zh: "放棄", pos: "v.", eg: "Never abandon your dream." },
            { en: "challenge", zh: "挑戰", pos: "n.", eg: "It is a big challenge." }
        ]));
        localStorage.setItem('vocab_state_vocab_system_test', JSON.stringify({
            mistakes: {
                "abandon": { mistakesCount: 2, correctCount: 0, data: { en: "abandon", zh: "放棄", pos: "v.", eg: "Never abandon your dream." } }
            },
            historicalMistakes: {},
            streak: { count: 12, lastDate: "" },
            currentDay: 1
        }));
    """)
    print("[Step 1] Reloading page to apply mock data...")
    driver.refresh()
    time.sleep(2)

    print("[Step 1] Verifying Dashboard UI...")
    assert len(driver.title) > 0, "Title check failed!"
    driver.save_screenshot(os.path.join(screenshot_dir, "system_verify_dashboard.png"))
    print("[Step 1] Dashboard loaded and verified successfully.")

    # --- STEP 2: DICTIONARY SEARCH ---
    print("[Step 2] Testing Online Dictionary Search...")
    driver.execute_script("""
        document.querySelectorAll('button').forEach(b => {
            if (b.textContent.includes('新增單字')) b.click();
        });
    """)
    time.sleep(1)

    print("[Step 2] Entering query 'success' into input...")
    search_input = wait.until(EC.visibility_of_element_located((By.XPATH, '//div[contains(@class, "fixed")]//input[@type="text"]')))
    search_input.send_keys("success")
    search_input.send_keys(Keys.ENTER)
    
    print("[Step 2] Waiting for dictionary search results from API...")
    time.sleep(4)  # Wait for API query to return

    driver.save_screenshot(os.path.join(screenshot_dir, "system_verify_dictionary.png"))
    assert "Definition" in driver.page_source or "definition" in driver.page_source.lower(), "Dictionary results not loaded!"
    print("[Step 2] Dictionary results loaded successfully.")

    print("[Step 2] Closing dictionary modal...")
    close_dict = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="✕"]')))
    close_dict.click()
    time.sleep(0.5)

    # --- STEP 3: SCANNING / QUICK FILTER FLOW ---
    print("[Step 3] Testing Quick Filter (Scanning View)...")
    driver.execute_script("""
        document.querySelectorAll('button').forEach(b => {
            if (b.textContent.includes('今日特訓')) b.click();
        });
    """)
    time.sleep(1)

    is_scanning = driver.execute_script("return document.body.innerText.includes('快速篩選')")
    assert is_scanning, "Not in scanning mode!"
    driver.save_screenshot(os.path.join(screenshot_dir, "system_verify_scanning.png"))
    print("[Step 3] Successfully entered scanning view.")

    print("[Step 3] Querying word from card...")
    card_dict_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="查詢此單字字典"]')))
    card_dict_btn.click()
    time.sleep(4)
    assert "Definition" in driver.page_source or "definition" in driver.page_source.lower(), "Card dictionary lookup failed!"

    print("[Step 3] Closing modal and returning to dashboard...")
    close_dict2 = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="✕"]')))
    close_dict2.click()
    time.sleep(0.5)

    driver.execute_script("""
        document.querySelectorAll('button').forEach(b => {
            if (b.textContent.includes('暫停存檔')) b.click();
        });
    """)
    time.sleep(0.5)
    wait.until(EC.alert_is_present())
    alert = driver.switch_to.alert
    alert.accept()
    time.sleep(1)
    print("[Step 3] Quick Filter flow completed successfully.")

    # --- STEP 4: SPELLING QUIZ AND ERROR PENALTY FLOW ---
    print("[Step 4] Testing Spelling Quiz Flow...")
    driver.execute_script("""
        document.querySelectorAll('button').forEach(b => {
            if (b.textContent.includes('錯題大會考')) b.click();
        });
    """)
    time.sleep(1)

    is_spelling = driver.execute_script("return document.body.innerText.includes('盲測')")
    assert is_spelling, "Not in spelling mode!"

    # Verify example sentence masks the target word "abandon"
    assert "Never ______ your dream." in driver.page_source, "Target word in spelling example was not masked!"
    print("[Step 4] Confirmed example sentence is masked correctly.")

    # Typo 1: Enter incorrect spelling
    print("[Step 4] Simulating Typo 1 (abanden)...")
    spelling_input = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@spellcheck="false"]')))
    spelling_input.send_keys("abanden")
    submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
    submit_btn.click()
    time.sleep(1.5)

    is_warning = driver.execute_script("return document.body.innerText.includes('手滑警告')")
    assert is_warning, "Typo warning not displayed!"
    driver.save_screenshot(os.path.join(screenshot_dir, "system_verify_spelling_warning.png"))
    print("[Step 4] Typo warning displays correctly.")

    # Typo 2: Enter incorrect spelling again for copy penalty
    print("[Step 4] Simulating Typo 2 (abandun) to trigger copy penalty...")
    spelling_input = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@spellcheck="false"]')))
    spelling_input.clear()
    spelling_input.send_keys("abandun")
    submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
    submit_btn.click()
    time.sleep(1.5)

    is_copy = driver.execute_script("return document.body.innerText.includes('請重抄') || document.body.innerText.includes('手寫記下')")
    assert is_copy, "Force copy penalty not displayed!"
    driver.save_screenshot(os.path.join(screenshot_dir, "system_verify_spelling_copy.png"))
    print("[Step 4] Force-copy penalty modal displays correctly.")

    # Correct spelling to clear penalty
    print("[Step 4] Entering correct spelling (abandon)...")
    spelling_input = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@spellcheck="false"]')))
    spelling_input.clear()
    spelling_input.send_keys("abandon")
    submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
    submit_btn.click()
    time.sleep(1.5)

    print("[Step 4] Verifying spelling summary page...")
    is_summary = driver.execute_script("return document.body.innerText.includes('完美結束')")
    assert is_summary, "Not in summary view!"

    print("[Step 4] Returning to dashboard...")
    driver.execute_script("""
        document.querySelectorAll('button').forEach(b => {
            if (b.textContent.includes('回到指揮中心') || b.textContent.includes('回到')) b.click();
        });
    """)
    time.sleep(1)
    print("[Step 4] Spelling quiz and penalty flow completed successfully.")

    # --- STEP 5: IMPORT PLAIN JSON WORD LIST ARRAY ---
    print("[Step 5] Testing JSON Word List Array Import...")
    temp_json_path = os.path.join(screenshot_dir, "temp_import.json")
    mock_words = [
        { "en": "verify", "pos": "v.", "zh": "驗證", "eg": "We need to verify this feature." },
        { "en": "success", "pos": "n.", "zh": "成功", "eg": "Hard work leads to success." }
    ]
    with open(temp_json_path, 'w', encoding='utf-8') as f:
        json.dump(mock_words, f, ensure_ascii=False)
        
    print("[Step 5] Selecting JSON file for import...")
    file_input = driver.find_element(By.XPATH, '//input[@type="file" and @accept=".json"]')
    file_input.send_keys(temp_json_path)
    time.sleep(1)
    
    print("[Step 5] Accepting import confirmation dialog...")
    wait.until(EC.alert_is_present())
    alert2 = driver.switch_to.alert
    alert2.accept()
    time.sleep(1.5)
    
    print("[Step 5] Accepting import success dialog...")
    wait.until(EC.alert_is_present())
    alert3 = driver.switch_to.alert
    alert3.accept()
    time.sleep(1)
    
    driver.save_screenshot(os.path.join(screenshot_dir, "system_verify_import.png"))
    
    # Verify imported data
    imported_len = driver.execute_script("return JSON.parse(localStorage.getItem('vocab_customVocab_vocab_system_test')).length")
    print(f"[Step 5] Words in localStorage: {imported_len}")
    assert imported_len == 2, f"Word list length mismatch! Expected 2, got {imported_len}"
    
    has_preview_btn = driver.execute_script("return document.body.innerText.includes('預覽字庫 (2')")
    assert has_preview_btn, "Dashboard word count preview mismatch!"
    print("[Step 5] JSON Word List import verified successfully!")
    
    # Clean up temp file
    if os.path.exists(temp_json_path):
        os.remove(temp_json_path)

    print("\n==================================================")
    print("All System Test cases passed successfully!")
    print("==================================================")

except Exception as e:
    import traceback
    print(f"\n[Error] System test failure: {type(e).__name__}: {e}")
    traceback.print_exc()
    try:
        print(f"[Error Info] Current URL: {driver.current_url}")
        driver.save_screenshot(os.path.join(screenshot_dir, "system_verify_error.png"))
    except Exception as inner_e:
        print(f"[Error Info] Failed to collect error context: {inner_e}")
    sys.exit(1)
finally:
    print("[Main] Closing WebDriver...")
    try:
        driver.quit()
    except Exception as e:
        print(f"[Main] Error closing WebDriver: {e}")
    if httpd:
        print("[Main] Shutting down web server...")
        try:
            httpd.shutdown()
            httpd.server_close()
            print("[Main] Web server shut down successfully.")
        except Exception as e:
            print(f"[Main] Error shutting down web server: {e}")
