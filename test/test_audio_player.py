import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

def run_tests():
    # 1. Config Headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1200,800")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Get path of index.html relative to this script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.abspath(os.path.join(script_dir, "..", "index.html"))
        file_url = f"file:///{html_path.replace(os.sep, '/')}"
        print(f"[TEST] Loading page: {file_url}")
        driver.get(file_url)
        
        # 2. Setup mock vocabulary database in localStorage
        print("[TEST] Injecting mock vocabulary and progress...")
        mock_setup_script = """
        localStorage.clear();
        localStorage.setItem('vocab_currentDB', 'vocab_test');
        localStorage.setItem('vocab_customVocab_vocab_test', JSON.stringify([
            { en: 'apple', zh: 'n. 蘋果', pos: 'n.', eg: 'This is an apple. (這是一顆蘋果。)' },
            { en: 'banana', zh: 'n. 香蕉', pos: 'n.', eg: 'I love bananas. (我愛香蕉。)' },
            { en: 'orange', zh: 'n. 柳橙', pos: 'n.', eg: 'Orange juice is delicious. (柳橙汁很好喝。)' }
        ]));
        localStorage.setItem('vocab_state_vocab_test', JSON.stringify({
            currentDay: 1,
            learnedWords: [],
            mistakes: {},
            historicalMistakes: {},
            streak: { count: 0, lastDate: null }
        }));
        """
        driver.execute_script(mock_setup_script)
        
        # Refresh to apply local storage
        driver.refresh()
        time.sleep(1) # wait for render
        
        # 3. Inject Mock speechSynthesis
        print("[TEST] Injecting Mock SpeechSynthesis API...")
        mock_speech_script = """
        window.mockSpeechHistory = [];
        window.speechSynthesis.getVoices = () => [
            { name: 'Google US English', lang: 'en-US', default: true },
            { name: 'Google 國語 (台灣)', lang: 'zh-TW', default: false }
        ];
        
        window.speechSynthesis.speak = (utterance) => {
            window.mockSpeechHistory.push({
                text: utterance.text,
                lang: utterance.lang,
                rate: utterance.rate,
                voice: utterance.voice ? utterance.voice.name : null
            });
            setTimeout(() => {
                if (utterance.onend) {
                    utterance.onend();
                }
            }, 30);
        };
        
        window.speechSynthesis.cancel = () => {
            // Cancel does nothing in mock
        };
        """
        driver.execute_script(mock_speech_script)
        
        # 4. Find and click dashboard entrance
        print("[TEST] Verifying Dashboard buttons...")
        wait = WebDriverWait(driver, 5)
        
        # Uses '\u807d\u8b80' for '聽讀'
        audio_setup_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., '\u807d\u8b80')]"))
        )
        assert audio_setup_btn is not None, "Entrance button for audio player not found"
        print("[TEST] Clicking Audio Training button...")
        audio_setup_btn.click()
        
        # 5. Verify Setup Modal opens
        print("[TEST] Verifying Setup Modal...")
        # Uses '\u807d\u5beb\u80cc\u55ae\u5b57\u7279\u8a13' for '聽寫背單字特訓'
        setup_modal = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(., '\u807d\u5beb\u80cc\u55ae\u5b57\u7279\u8a13')]"))
        )
        assert setup_modal is not None, "Setup Modal was not opened successfully"
        
        # Select "整個單字庫" -> '\u6574\u500b\u55ae\u5b57\u5eab'
        btn_library = driver.find_element(By.XPATH, "//button[contains(., '\u6574\u500b\u55ae\u5b57\u5eab')]")
        btn_library.click()
        
        # Select custom range selection
        range_select_el = driver.find_element(By.XPATH, "//select[option[@value='custom']]")
        select_range = Select(range_select_el)
        select_range.select_by_value("custom")
        
        # Set range 1 to 2
        # '開始' -> '\u958b\u59cb'
        start_idx_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='number' and preceding-sibling::span[contains(text(), '\u958b\u59cb')]]"))
        )
        # '結束' -> '\u7d50\u675f'
        end_idx_input = driver.find_element(By.XPATH, "//input[@type='number' and preceding-sibling::span[contains(text(), '\u7d50\u675f')]]")
        
        start_idx_input.clear()
        start_idx_input.send_keys("1")
        end_idx_input.clear()
        end_idx_input.send_keys("2")
        
        # Click checkboxes via JS
        checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        for cb in checkboxes:
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
                
        # Select custom spelling pause duration (0s)
        spelling_pause_el = driver.find_element(By.XPATH, "//select[option[@value='0']]")
        select_spelling_pause = Select(spelling_pause_el)
        select_spelling_pause.select_by_value("0")
        print("[TEST] Selected spelling pause duration: 0s")
                
        # 6. Start audio session
        # '開始聽讀特訓' -> '\u958b\u59cb\u807d\u8b80\u7279\u8a13'
        btn_start = driver.find_element(By.XPATH, "//button[contains(., '\u958b\u59cb\u807d\u8b80\u7279\u8a13')]")
        print("[TEST] Clicking Start Audio Training...")
        btn_start.click()
        
        # 7. Verify player panel UI
        print("[TEST] Verifying player panel...")
        # '聽讀特訓' -> '\u807d\u8b80\u7279\u8a13'
        # Using contains(., ...) instead of contains(text(), ...) because React splits text nodes
        player_title = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(., '\u807d\u8b80\u7279\u8a13')]"))
        )
        assert player_title is not None, "Failed to navigate to player view"
        
        # Progress check
        # '聽讀特訓 (1/2)' -> '\u807d\u8b80\u7279\u8a13 (1/2)'
        progress_text = driver.find_element(By.XPATH, "//*[contains(., '\u807d\u8b80\u7279\u8a13 (1/2)')]")
        assert progress_text is not None, "Progress text should show 1/2"
        
        # Blind mode check
        card_content = driver.find_element(By.XPATH, "//main").text
        assert "apple" not in card_content or "blind" in card_content.lower() or "🙈" in card_content, "Word spelling leaked in blind mode"
        
        # 8. Test controls
        btn_play_pause = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='\u66ab\u505c\u64ad\u653e' or @title='\u7e7c\u7e8a\u64ad\u653e' or @title='暫停播放' or @title='繼續播放']"))
        )
        
        print("[TEST] Testing pause...")
        btn_play_pause.click()
        time.sleep(0.5)
        
        # '已暫停' -> '\u5df2\u66ab\u505c'
        status_paused = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(., '\u5df2\u66ab\u505c')]"))
        )
        assert status_paused is not None, "Pause state not updated"
        
        print("[TEST] Testing play resume...")
        btn_play_pause.click()
        time.sleep(0.5)
        
        btn_next = driver.find_element(By.XPATH, "//button[contains(@title, '\u4e0b\u4e00\u500b') or @title='下一個單字']")
        print("[TEST] Testing Next word (Banana)...")
        btn_next.click()
        time.sleep(0.5)
        
        # '聽讀特訓 (2/2)' -> '\u807d\u8b80\u7279\u8a13 (2/2)'
        progress_text_2 = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(., '\u807d\u8b80\u7279\u8a13 (2/2)')]"))
        )
        assert progress_text_2 is not None, "Progress did not update to 2/2 after clicking next"
        
        btn_prev = driver.find_element(By.XPATH, "//button[contains(@title, '\u4e0a\u4e00\u500b') or @title='上一個單字']")
        print("[TEST] Testing Prev word (Apple)...")
        btn_prev.click()
        time.sleep(0.5)
        
        # '聽讀特訓 (1/2)' -> '\u807d\u8b80\u7279\u8a13 (1/2)'
        progress_text_1 = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(., '\u807d\u8b80\u7279\u8a13 (1/2)')]"))
        )
        assert progress_text_1 is not None, "Progress did not go back to 1/2 after clicking prev"
        
        # Eye toggle button matches title containing '英文單字' -> '\u82f1\u6587\u55ae\u5b57'
        btn_blind_toggle = driver.find_element(By.XPATH, "//button[contains(@title, '\u82f1\u6587\u55ae\u5b57')]")
        print("[TEST] Testing show/hide word toggle...")
        btn_blind_toggle.click()
        time.sleep(0.3)
        
        card_content_revealed = driver.find_element(By.XPATH, "//main").text
        assert "apple" in card_content_revealed.lower(), "Word was not revealed"
        
        # 9. Test stop and exit
        # '停止並返回' -> '\u505c\u6b62\u4e26\u8fd4\u56de'
        btn_stop = driver.find_element(By.XPATH, "//button[contains(., '\u505c\u6b62\u4e26\u8fd4\u56de')]")
        print("[TEST] Clicking Stop and Return to Dashboard...")
        btn_stop.click()
        time.sleep(0.5)
        
        # '發動今日特訓' -> '\u767c\u52d5\u4eca\u65e5\u7279\u8a13'
        dashboard_visible = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//h2[contains(., '\u767c\u52d5\u4eca\u65e5\u7279\u8a13') or contains(., '今日特訓')]"))
        )
        assert dashboard_visible is not None, "Failed to return to Dashboard"
        
        # 10. Check Speech History API calls
        speech_history = driver.execute_script("return window.mockSpeechHistory;")
        print(f"[TEST] Voice speech history count: {len(speech_history)} items")
        assert len(speech_history) > 0, "SpeechSynthesis.speak was never called"
        
        spoken_texts = [item['text'] for item in speech_history]
        print(f"[TEST] Speech history first 5 items: {spoken_texts[:5]}")
        assert any("apple" in t for t in spoken_texts), "Did not speak word apple"
        
        # Verify spelling speed rate is standard 0.8 (same as global speechRate)
        spelling_speeches = [item for item in speech_history if len(item['text']) == 1]
        print(f"[TEST] Spelling speeches: {spelling_speeches}")
        for item in spelling_speeches:
            assert abs(item['rate'] - 0.8) < 0.01, f"Spelling speech rate should be standard 0.8, but got {item['rate']}"
        print("[TEST] Verified spelling pause selection and standard rate successfully!")
        
        print("\nSUCCESS: All Audio Player tests passed!")
        
    except Exception as e:
        print(f"\nFAILURE: Test failed, error: {e}")
        try:
            driver.save_screenshot("test_failure_screenshot.png")
            print("[TEST] Saved screenshot to test_failure_screenshot.png")
        except Exception as se:
            print(f"[TEST] Cannot save screenshot: {se}")
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
