import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_visible_text(driver):
    return driver.execute_script("""
        const clone = document.body.cloneNode(true);
        clone.querySelectorAll('script, style').forEach(s => s.remove());
        return clone.textContent;
    """)

def run_tests():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1200,800")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 5)
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.abspath(os.path.join(script_dir, "..", "index.html"))
        file_url = f"file:///{html_path.replace(os.sep, '/')}"
        
        driver.get(file_url)
        
        # Setup localStorage context with custom casing words
        driver.execute_script("""
            localStorage.clear();
            localStorage.setItem('vocab_currentDB', 'vocab_test');
            localStorage.setItem('vocab_customVocab_vocab_test', JSON.stringify([
                { en: 'apple', zh: 'n. 蘋果', pos: 'n.', eg: 'This is an apple. (這是一顆蘋果。)' },
                { en: 'Banana', zh: 'n. 香蕉', pos: 'n.', eg: 'I love Bananas. (我愛香蕉。)' },
                { en: 'cat', zh: 'n. 貓', pos: 'n.', eg: 'The cat is sleeping. (貓咪在睡覺。)' },
                { en: 'dog', zh: 'n. 狗', pos: 'n.', eg: 'My dog is friendly. (我的狗很友善。)' },
                { en: 'ElePHant', zh: 'n. 大象', pos: 'n.', eg: 'The ElePHant is big. (大象很大隻。)' }
            ]));
            localStorage.setItem('vocab_wordsPerDay_vocab_test', '10');
            localStorage.setItem('vocab_ghostsPerDay_vocab_test', '0');
            localStorage.setItem('vocab_audioSettings', JSON.stringify({
                repeats: 1,
                wordPause: 0.1,
                spellingPause: 0,
                readExample: true,
                volume: 80,
                enVoiceName: '',
                zhVoiceName: ''
            }));
            localStorage.setItem = () => {};
        """)
        
        driver.refresh()
        time.sleep(1.0)
        
        # Inject API mocks
        mock_js = """
        window.mockAlerts = [];
        window.alert = (msg) => { window.mockAlerts.push(msg); };
        window.mockConfirms = [];
        window.confirm = (msg) => { window.mockConfirms.push(msg); return true; };
        
        window.mockSpeechHistory = [];
        window.speechSynthesis.getVoices = () => [
            { name: 'Google US English', lang: 'en-US', default: true },
            { name: 'Google 國語 (台灣)', lang: 'zh-TW', default: false }
        ];
        window.speechSynthesis.speak = (utterance) => {
            window.mockSpeechHistory.push({
                text: utterance.text,
                lang: utterance.lang,
                rate: utterance.rate
            });
            setTimeout(() => { if (utterance.onend) utterance.onend(); }, 10);
        };
        window.speechSynthesis.cancel = () => {};
        """
        driver.execute_script(mock_js)
        time.sleep(0.5)
        
        # Open Audio Player Dialog
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('聽讀'));
            if (btn) btn.click();
            else throw new Error('Audio training button not found');
        """)
        time.sleep(0.5)
        
        # Verify Setup Modal
        visible_text = get_visible_text(driver)
        assert "聽寫背單字特訓" in visible_text or "語音人" in visible_text, "Setup Modal was not opened successfully"
        
        # Configure player range and settings
        driver.execute_script("""
            const modal = Array.from(document.querySelectorAll('.fixed.inset-0')).find(m => m.textContent.includes('聽寫背單字特訓'));
            if (!modal) throw new Error('Audio setup modal not found in DOM');
            
            const sourceBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('整個單字庫'));
            if (sourceBtn) sourceBtn.click();
            
            const selectEl = modal.querySelector('select');
            if (selectEl) {
                const option = Array.from(selectEl.options).find(o => o.value === 'custom');
                if (option) {
                    option.selected = true;
                    selectEl.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        """)
        time.sleep(0.6)
        
        driver.execute_script("""
            const modal = Array.from(document.querySelectorAll('.fixed.inset-0')).find(m => m.textContent.includes('聽寫背單字特訓'));
            if (!modal) throw new Error('Audio setup modal not found in DOM');
            
            const findInputByLabel = (labelText) => {
                const span = Array.from(modal.querySelectorAll('span')).find(s => s.textContent.includes(labelText));
                return span ? span.parentElement.querySelector('input') : null;
            };
            
            const startInput = findInputByLabel('開始編號');
            const endInput = findInputByLabel('結束編號');
            
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            if (startInput) {
                setter.call(startInput, '1');
                startInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (endInput) {
                setter.call(endInput, '5');
                endInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            const checkbox = modal.querySelector('input[type="checkbox"]');
            console.log('[TEST] Checkbox state before:', checkbox ? checkbox.checked : 'null');
            if (checkbox && !checkbox.checked) {
                checkbox.parentElement.click();
                console.log('[TEST] Checkbox state after click:', checkbox.checked);
            }
            
            const selects = Array.from(modal.querySelectorAll('select'));
            if (selects.length >= 2) {
                const selectSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
                selectSetter.call(selects[1], '0');
                selects[1].dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            const startBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('開始聽讀特訓'));
            if (startBtn) startBtn.click();
        """)
        time.sleep(2.5)
        
        # Verify player panel active
        progress_text = driver.execute_script("return document.querySelector('main').textContent;")
        assert "聽讀特訓" in progress_text or "1/5" in progress_text, "Failed to navigate to audio player view"
        
        # Let the player automatically step through all 5 words
        time.sleep(10.0)
        
        # Stop and return
        btn_stop = driver.find_element(By.XPATH, "//button[contains(., '停止並返回')]")
        btn_stop.click()
        time.sleep(1.0)
        
        # Verify spoken history casing and translations
        history = driver.execute_script("return window.mockSpeechHistory;")
        spoken_texts = [item['text'] for item in history]
        
        assert "Banana" in spoken_texts, "Casing was not retained for 'Banana'"
        assert "ElePHant" in spoken_texts, "Casing was not retained for 'ElePHant'"
        assert "BANANA" not in spoken_texts, "Forced uppercase detected for 'Banana'"
        assert "ELEPHANT" not in spoken_texts, "Forced uppercase detected for 'ElePHant'"
        
        # Check translation silence in example sentences
        assert "This is an apple." in spoken_texts, "English example sentence for 'apple' not spoken"
        assert "I love Bananas." in spoken_texts, "English example sentence for 'Banana' not spoken"
        assert "The ElePHant is big." in spoken_texts, "English example sentence for 'ElePHant' not spoken"
        
        for text in spoken_texts:
            assert "這是一顆蘋果" not in text, "Chinese translation of example sentence 'apple' was spoken!"
            assert "我愛香蕉" not in text, "Chinese translation of example sentence 'Banana' was spoken!"
            assert "大象很大隻" not in text, "Chinese translation of example sentence 'ElePHant' was spoken!"
            assert "（" not in text and "）" not in text, "Parentheses characters leaked into speech!"
            assert "(" not in text and ")" not in text, "Parentheses characters leaked into speech!"
            
        # Success output is minimal to save token
        print("[SUCCESS] test_audio_casing_rules passed.")
        
    except Exception as e:
        print(f"\n[FAILURE] test_audio_casing_rules failed, error: {e}", file=sys.stderr)
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Save screenshot
            screenshot_path = os.path.join(current_dir, "test_audio_casing_rules_failure.png")
            driver.save_screenshot(screenshot_path)
            print(f"[TEST] Saved failure screenshot to {screenshot_path}", file=sys.stderr)
            
            # Save page source to local file
            source_path = os.path.join(current_dir, "failure_source.html")
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"[TEST] Saved failure page source to {source_path}", file=sys.stderr)
            
            # Extract and print mock speech history for debugging
            history = driver.execute_script("return window.mockSpeechHistory || [];")
            print(f"[DEBUG] Spoken texts was: {[item.get('text') for item in history]}", file=sys.stderr)
            
            # Extract and print browser console logs for debugging
            try:
                logs = driver.get_log('browser')
                print(f"[DEBUG] Browser logs: {logs}", file=sys.stderr)
            except Exception as le:
                pass
        except Exception as se:
            print(f"[TEST] Cannot save failure diagnostics: {se}", file=sys.stderr)
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
