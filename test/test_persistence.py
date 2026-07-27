import time
import os
import sys
import socketserver
import http.server
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRECTORY = os.path.abspath(os.path.join(BASE_DIR, "..", "www"))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
PORT = httpd.server_address[1]
print(f"[Test] Starting server on port {PORT} serving '{DIRECTORY}'...")
server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
server_thread.start()

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 8)

try:
    target_url = f"http://127.0.0.1:{PORT}/index.html"
    driver.get(target_url)
    time.sleep(1)

    print("[Test] Setting mock tempSession into localStorage...")
    driver.execute_script("""
        localStorage.clear();
        localStorage.setItem('vocab_currentDB', 'vocab_2000');
        localStorage.setItem('vocab_tempSession_vocab_2000', JSON.stringify({
            date: new Date().toDateString(),
            view: 'spelling',
            sessionType: 'daily',
            queue: [
                { en: "acknowledge", zh: "確認/承認", pos: "v.", eg: "Please acknowledge receipt." }
            ],
            currentSessionWords: [
                { en: "acknowledge", zh: "確認/承認", pos: "v.", eg: "Please acknowledge receipt." }
            ],
            spellingState: {
                userInput: "ackno",
                typoCount: 1,
                mustTypeCorrectly: false,
                copyFailCount: 0
            }
        }));
    """)

    print("[Test] Refreshing page to trigger session restore prompt...")
    driver.refresh()
    time.sleep(1)

    # Handle window.confirm alert automatically
    alert = wait.until(EC.alert_is_present())
    print(f"[Test] Confirm alert text: '{alert.text}'")
    alert.accept()
    time.sleep(2)

    print("[Test] Verifying restored state...")
    input_elem = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@spellcheck="false"]')))
    restored_val = input_elem.get_attribute("value")
    print(f"[Test] Restored userInput: '{restored_val}'")
    assert restored_val == "ackno", f"Expected 'ackno', got '{restored_val}'"

    is_warning = driver.execute_script("return document.body.innerText.includes('手滑警告')")
    assert is_warning, "Restored typoCount state badge missing!"
    print("[Test] Typo warning badge correctly restored!")

    # Check viewport tag
    meta_viewport = driver.find_element(By.XPATH, '//meta[@name="viewport"]').get_attribute("content")
    print(f"[Test] Viewport content: '{meta_viewport}'")
    assert "user-scalable=yes" in meta_viewport, "Viewport user-scalable=yes missing!"

    print("[Test] Persistence and restoration test PASSED successfully!")

finally:
    driver.quit()
    httpd.shutdown()
    httpd.server_close()
    print("[Test] Server shut down.")
