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
        driver.refresh()
        time.sleep(1)
        
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
        
        window.speechSynthesis.cancel = () => {};
        """
        driver.execute_script(mock_speech_script)
        
        wait = WebDriverWait(driver, 5)
        audio_setup_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., '\u807d\u8b80')]"))
        )
        audio_setup_btn.click()
        
        setup_modal = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(., '\u807d\u5beb\u80cc\u55ae\u5b57\u7279\u8a13')]"))
        )
        assert setup_modal is not None
        
        btn_library = driver.find_element(By.XPATH, "//button[contains(., '\u6574\u500b\u55ae\u5b57\u5eab')]")
        btn_library.click()
        
        range_select_el = driver.find_element(By.XPATH, "//select[option[@value='custom']]")
        select_range = Select(range_select_el)
        select_range.select_by_value("custom")
        
        start_idx_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='number' and preceding-sibling::span[contains(text(), '\u958b\u59cb')]]"))
        )
        end_idx_input = driver.find_element(By.XPATH, "//input[@type='number' and preceding-sibling::span[contains(text(), '\u7d50\u675f')]]")
        
        start_idx_input.clear()
        start_idx_input.send_keys("1")
        end_idx_input.clear()
        end_idx_input.send_keys("2")
        
        checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        for cb in checkboxes:
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
                
        spelling_pause_el = driver.find_element(By.XPATH, "//select[option[@value='0']]")
        select_spelling_pause = Select(spelling_pause_el)
        select_spelling_pause.select_by_value("0")
                
        btn_start = driver.find_element(By.XPATH, "//button[contains(., '\u958b\u59cb\u807d\u8b80\u7279\u8a13')]")
        btn_start.click()
        
        player_title = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(., '\u807d\u8b80\u7279\u8a13')]"))
        )
        assert player_title is not None
        
        progress_text = driver.find_element(By.XPATH, "//*[contains(., '\u807d\u8b80\u7279\u8a13 (1/2)')]")
        assert progress_text is not None
        
        card_content = driver.find_element(By.XPATH, "//main").text
        assert "apple" not in card_content or "blind" in card_content.lower() or "🙈" in card_content
        
        btn_play_pause = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='\u66ab\u505c\u64ad\u653e' or @title='\u7e7c\u7e8a\u64ad\u653e' or @title='暫停播放' or @title='繼續播放']"))
        )
        btn_play_pause.click()
        time.sleep(0.5)
        
        status_paused = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(., '\u5df2\u66ab\u505c')]"))
        )
        assert status_paused is not None
        
        btn_play_pause.click()
        time.sleep(0.5)
        
        btn_next = driver.find_element(By.XPATH, "//button[contains(@title, '\u4e0b\u4e00\u500b') or @title='下一個單字']")
        btn_next.click()
        time.sleep(0.5)
        
        progress_text_2 = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(., '\u807d\u8b80\u7279\u8a13 (2/2)')]"))
        )
        assert progress_text_2 is not None
        
        btn_prev = driver.find_element(By.XPATH, "//button[contains(@title, '\u4e0a\u4e00\u500b') or @title='上一個單字']")
        btn_prev.click()
        time.sleep(0.5)
        
        progress_text_1 = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(., '\u807d\u8b80\u7279\u8a13 (1/2)')]"))
        )
        assert progress_text_1 is not None
        
        btn_blind_toggle = driver.find_element(By.XPATH, "//button[contains(@title, '\u82f1\u6587\u55ae\u5b57')]")
        btn_blind_toggle.click()
        time.sleep(0.3)
        
        card_content_revealed = driver.find_element(By.XPATH, "//main").text
        assert "apple" in card_content_revealed.lower()
        
        btn_stop = driver.find_element(By.XPATH, "//button[contains(., '\u505c\u6b62\u4e26\u8fd4\u56de')]")
        btn_stop.click()
        time.sleep(0.5)
        
        dashboard_visible = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//h2[contains(., '\u767c\u52d5\u4eca\u65e5\u7279\u8a13') or contains(., '今日特訓')]"))
        )
        assert dashboard_visible is not None
        
        speech_history = driver.execute_script("return window.mockSpeechHistory;")
        assert len(speech_history) > 0
        
        spoken_texts = [item['text'] for item in speech_history]
        assert any("apple" in t for t in spoken_texts)
        
        spelling_speeches = [item for item in speech_history if len(item['text']) == 1]
        for item in spelling_speeches:
            assert abs(item['rate'] - 0.8) < 0.01
            
        print("[SUCCESS] test_audio_player passed.")
        
    except Exception as e:
        print(f"\n[FAILURE] test_audio_player failed, error: {e}", file=sys.stderr)
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Save screenshot
            screenshot_path = os.path.join(current_dir, "test_audio_player_failure.png")
            driver.save_screenshot(screenshot_path)
            print(f"[TEST] Saved screenshot to {screenshot_path}", file=sys.stderr)
            
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
