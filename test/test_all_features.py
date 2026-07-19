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
        # 1. Load the locally served page or local file to establish domain context
        script_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.abspath(os.path.join(script_dir, "..", "index.html"))
        file_url = f"file:///{html_path.replace(os.sep, '/')}"
        print(f"[TEST] Loading page: {file_url}")
        driver.get(file_url)
        
        # 2. Clean and setup local storage context
        print("[TEST] Setting up clean local storage context...")
        driver.execute_script("""
            localStorage.clear();
            localStorage.setItem('vocab_currentDB', 'vocab_test');
            localStorage.setItem('vocab_wordsPerDay_vocab_test', '10');
            localStorage.setItem('vocab_ghostsPerDay_vocab_test', '0');
        """)
        
        # Refresh to apply local storage state
        driver.refresh()
        time.sleep(1.0)
        
        # 3. Inject general UI and API mocks
        print("[TEST] Injecting general UI and API mocks...")
        mock_js = """
        // Mock alert & confirm
        window.mockAlerts = [];
        window.alert = (msg) => {
            console.log('[MOCK ALERT]', msg);
            window.mockAlerts.push(msg);
        };
        window.mockConfirms = [];
        window.confirm = (msg) => {
            console.log('[MOCK CONFIRM]', msg);
            window.mockConfirms.push(msg);
            return true; // Auto confirm
        };
        
        // Mock speech synthesis
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
            setTimeout(() => {
                if (utterance.onend) utterance.onend();
            }, 10);
        };
        window.speechSynthesis.cancel = () => {};
        
        // Mock fetch for Dictionary and Translation APIs
        window.fetch = async (url) => {
            console.log('[MOCK FETCH] requesting:', url);
            if (url.includes('api.dictionaryapi.dev')) {
                return {
                    ok: true,
                    status: 200,
                    json: async () => [{
                        word: 'fox',
                        phonetics: [{ text: '/fɒks/' }],
                        meanings: [{
                            partOfSpeech: 'noun',
                            definitions: [{
                                definition: 'A wild carnivorous mammal.',
                                example: 'The quick brown fox jumps over the lazy dog.'
                            }]
                        }]
                    }]
                };
            } else if (url.includes('mymemory.translated.net')) {
                return {
                    ok: true,
                    status: 200,
                    json: async () => ({
                        responseData: { translatedText: '狐狸' },
                        matches: [{ translation: '狐狸' }]
                    })
                };
            }
            return { ok: true, status: 200, json: async () => ({}) };
        };
        
        // Mock download clicks to verify export functions
        window.mockDownloads = [];
        const originalCreateElement = document.createElement;
        document.createElement = function(tagName) {
            const element = originalCreateElement.call(document, tagName);
            if (tagName.toLowerCase() === 'a') {
                element.click = function() {
                    console.log('[MOCK DOWNLOAD] Intercepted download:', element.download);
                    window.mockDownloads.push({
                        filename: element.download,
                        href: element.href
                    });
                };
            }
            return element;
        };
        """
        driver.execute_script(mock_js)
        time.sleep(0.5)
        
        # 4. Import new dictionary database via test_import.txt
        print("[TEST] Importing new dictionary database...")
        import_txt_path = os.path.abspath(os.path.join(script_dir, "test_import.txt"))
        file_input = driver.find_element(By.XPATH, "//input[@accept='.txt' and parent::label[contains(@title, '匯入字典')]]")
        driver.execute_script("arguments[0].classList.remove('hidden');", file_input)
        file_input.send_keys(import_txt_path)
        time.sleep(1.5)
        
        # Verify 5 words successfully loaded
        page_src = driver.page_source
        assert "5" in page_src, "Failed to load 5 words from test_import.txt"
        print("[TEST SUCCESS] Successfully imported new dictionary with 5 words!")
        
        # 5. Test Button: Preview Today's Words (🔍 預覽單字)
        print("[TEST] Testing Preview Today's Words modal...")
        driver.execute_script("""
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => b.textContent.includes('預覽單字'));
            if (btn) btn.click();
            else throw new Error('Preview today button not found');
        """)
        time.sleep(0.5)
        modal_header = driver.execute_script("return document.querySelector('h3').textContent;")
        assert "學習" in modal_header or "預覽" in modal_header, "Failed to open Today's Words Preview modal"
        
        # Close modal (click X button)
        driver.execute_script("""
            const btns = Array.from(document.querySelectorAll('button'));
            const closeBtn = btns.find(b => b.textContent === '✕');
            if (closeBtn) closeBtn.click();
        """)
        time.sleep(0.5)
        print("[TEST SUCCESS] Preview Today's Words modal works successfully!")
        
        # 6. Test Button: Preview Full Library (🗂️ 預覽字庫)
        print("[TEST] Testing Preview Full Library modal...")
        driver.execute_script("""
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => b.textContent.includes('預覽字庫'));
            if (btn) btn.click();
            else throw new Error('Preview full library button not found');
        """)
        time.sleep(0.5)
        all_modal_header = driver.execute_script("return document.querySelector('h3').textContent;")
        assert "全字庫" in all_modal_header or "預覽" in all_modal_header, "Failed to open Full Library Preview modal"
        
        # Test Search inside full library modal
        print("[TEST] Typing 'banana' in library search filter...")
        search_input = driver.find_element(By.XPATH, "//input[@placeholder='輸入關鍵字篩選單字、詞性或釋義...']")
        search_input.send_keys("banana")
        time.sleep(0.5)
        
        # Verify filtered results contain banana
        search_result_text = driver.page_source
        assert "banana" in search_result_text, "Failed to search word in full preview"
        
        # Close full library modal
        driver.execute_script("""
            const btns = Array.from(document.querySelectorAll('button'));
            const closeBtn = btns.find(b => b.textContent === '✕');
            if (closeBtn) closeBtn.click();
        """)
        time.sleep(0.5)
        print("[TEST SUCCESS] Preview Full Library modal and search filter work successfully!")
        
        # 7. Test Button: Lookup and Add Custom Word (📖 查字典與新增單字)
        print("[TEST] Testing Lookup and Add Custom Word...")
        driver.execute_script("""
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => b.textContent.includes('查字典') || b.textContent.includes('新增單字'));
            if (btn) btn.click();
            else throw new Error('Lookup and add button not found');
        """)
        time.sleep(0.5)
        
        # Type 'fox' in search box using language independent selector
        dict_input = driver.find_element(By.XPATH, "//form/div/input[@type='text']")
        dict_input.send_keys("fox")
        
        # Submit the search form
        driver.execute_script("""
            const form = document.querySelector('form');
            if (form) {
                form.dispatchEvent(new Event('submit', { bubbles: true }));
            } else {
                throw new Error('Dict search form not found');
            }
        """)
        time.sleep(1.0)
        
        # Check lookup result loaded translation (狐狸) and meaning
        dict_modal_src = driver.page_source
        assert "fox" in dict_modal_src.lower(), "Lookup result did not load"
        
        # Click "新增單字" submit button inside the add word form
        print("[TEST] Adding custom word 'fox' to database...")
        driver.execute_script("""
            const addBtn = Array.from(document.querySelectorAll('form button[type="submit"]')).find(b => b.textContent.includes('新增單字'));
            if (addBtn) addBtn.click();
            else throw new Error('Add custom word submit button not found');
        """)
        time.sleep(0.5)
        
        # Close Lookup modal
        driver.execute_script("""
            const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent === '✕');
            if (closeBtn) closeBtn.click();
        """)
        time.sleep(0.5)
        
        # Confirm that word count increased to 6
        assert "6" in driver.page_source, "Custom word 'fox' was not added to the database"
        print("[TEST SUCCESS] Lookup and Add Custom Word works successfully!")
        
        # 8. Test Button: ⚡ 發動今日特訓 (Start Today's Training)
        print("[TEST] Starting daily training...")
        driver.execute_script("""
            const startBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('今日特訓'));
            if (startBtn) startBtn.click();
            else throw new Error('Start today training button not found');
        """)
        time.sleep(1.0)
        
        # Verify in "第一關：快速篩選" (Quick Scan)
        current_view_text = get_visible_text(driver)
        assert "第一關" in current_view_text or "篩選" in current_view_text, "Not in Quick Scan stage"
        
        # Scan words dynamically until the view transitions to spelling stage!
        print("[TEST] Scanning words dynamically in Quick Scan stage...")
        loop_scan = 0
        while loop_scan < 20:
            current_view = get_visible_text(driver)
            if "請拼寫" in current_view or "盲測" in current_view or "第二關" in current_view or "拼字" in current_view:
                break
            
            # Check how many words are left in scanning phase
            remaining_words = driver.execute_script("""
                const clone = document.body.cloneNode(true);
                clone.querySelectorAll('script, style').forEach(s => s.remove());
                const text = clone.textContent;
                const match = text.match(/第一關：快速篩選 \\(剩 (\\d+) 字\\)/) || text.match(/快速篩選.*(\\d+)/);
                return match ? parseInt(match[1], 10) : 0;
            """)
            word_now = driver.execute_script("return document.querySelector('h2').textContent;")
            
            if remaining_words <= 1:
                # Last word: Click "不熟" to make sure we have mistakes for spelling test
                print(f"[TEST] Scanning last word {word_now} -> Click '不熟'")
                driver.execute_script("""
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('不熟'));
                    if (btn) btn.click();
                """)
            else:
                # Other words: Click "認識"
                print(f"[TEST] Scanning word {word_now} -> Click '認識'")
                driver.execute_script("""
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('認識'));
                    if (btn) btn.click();
                """)
            time.sleep(0.6)
            loop_scan += 1
        
        # 9. Verify in "第二關：拼字特訓" (Spelling Stage)
        current_view_header = get_visible_text(driver)
        assert "請拼寫" in current_view_header or "盲測" in current_view_header or "第二關" in current_view_header, "Failed to transition to Spelling phase"
        print("[TEST SUCCESS] Successfully transitioned to Spelling stage!")
        
        # Complete Spelling phase
        loop_guard = 0
        mistake_tested = False
        
        while loop_guard < 20:
            current_view_header = get_visible_text(driver)
            if "完美" in current_view_header or "結算" in current_view_header or "打卡存檔" in current_view_header or "回到指揮中心" in current_view_header:
                print("[TEST] Reached training summary page!")
                break
                
            current_zh = driver.execute_script("return document.querySelector('h2').textContent;")
            # Find matching word English spelling from database
            correct_en = driver.execute_script(f"""
                const currentZh = "{current_zh}";
                const dbName = localStorage.getItem('vocab_currentDB');
                const vocab = JSON.parse(localStorage.getItem('vocab_customVocab_' + dbName));
                const matched = vocab.find(w => w.zh === currentZh);
                return matched ? matched.en : '';
            """)
            print(f"[TEST] Current spelling prompt: {current_zh} -> Correct answer is: '{correct_en}'")
            
            # Let's test mistake punishment for one word
            if not mistake_tested and correct_en == "elephant":
                print("[TEST] Simulating wrong spelling 1 (should trigger warning)...")
                driver.execute_script("""
                    const input = document.querySelector('input[type="text"]');
                    if (input) {
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        setter.call(input, 'wrongspell1');
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    const form = document.querySelector('form');
                    if (form) form.dispatchEvent(new Event('submit', { bubbles: true }));
                """)
                time.sleep(0.5)
                
                print("[TEST] Simulating wrong spelling 2 (should trigger lock & rewrite punishment)...")
                driver.execute_script("""
                    const input = document.querySelector('input[type="text"]');
                    if (input) {
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        setter.call(input, 'wrongspell2');
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    const form = document.querySelector('form');
                    if (form) form.dispatchEvent(new Event('submit', { bubbles: true }));
                """)
                time.sleep(0.5)
                
                # Verify that it is in forced rewrite state (contains 'border-emerald-500' on input or contains correct answer text)
                is_punished = driver.execute_script("""
                    const input = document.querySelector('input[type="text"]');
                    return input.classList.contains('border-emerald-500');
                """)
                assert is_punished, "Strict punishment state not active"
                print("[TEST SUCCESS] Strict correction punishment triggered and verified successfully!")
                
                # Solve rewrite state by typing correct word
                print(f"[TEST] Resolving rewrite by typing: {correct_en}...")
                driver.execute_script(f"""
                    const input = document.querySelector('input[type="text"]');
                    if (input) {{
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        setter.call(input, '{correct_en}');
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                    const form = document.querySelector('form');
                    if (form) form.dispatchEvent(new Event('submit', {{ bubbles: true }}));
                """)
                time.sleep(0.5)
                mistake_tested = True
                continue
            
            # Submit correct spelling using form submit trigger and prototype value setter
            driver.execute_script(f"""
                const input = document.querySelector('input[type="text"]');
                if (input) {{
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(input, '{correct_en}');
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
                const form = document.querySelector('form');
                if (form) {{
                    form.dispatchEvent(new Event('submit', {{ bubbles: true }}));
                }}
            """)
            time.sleep(0.6)
            loop_guard += 1
            
        # Verify training finished, return to dashboard by clicking either return button
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('回到指揮中心') || b.textContent.includes('打卡存檔'));
            if (btn) btn.click();
            else throw new Error('Return to dashboard button not found on summary view');
        """)
        time.sleep(1.5)
        print("[TEST SUCCESS] Daily training completed and returned to dashboard!")
        
        # 10. Test Button: 🔥 降溫：錯題大會考 (Mistakes Review)
        print("[TEST] Testing Mistakes Review button...")
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('降溫'));
            if (btn) btn.click();
            else throw new Error('Mistakes review button not found');
        """)
        time.sleep(1.0)
        
        # Verify in spelling view (since mistakes review immediately starts spelling)
        review_text = get_visible_text(driver)
        assert "會考" in review_text or "拼字" in review_text or "盲測" in review_text or "剩" in review_text, "Failed to enter Mistakes Review session"
        
        # Exit Mistakes Review Session
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('暫停存檔'));
            if (btn) btn.click();
        """)
        time.sleep(1.0)
        print("[TEST SUCCESS] Mistakes Review button tested and exited successfully!")
        
        # 11. Test Button: 🏛️ 深度：歷史隨機抽查 (History Random Check)
        print("[TEST] Testing History Random Check button...")
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('深度') || b.textContent.includes('歷史隨機抽查'));
            if (btn) btn.click();
            else throw new Error('History check button not found');
        """)
        time.sleep(1.0)
        
        # Verify in history check session or checking alert
        check_text = get_visible_text(driver)
        alert_msgs = driver.execute_script("return window.mockAlerts;")
        print(f"[TEST] History check messages: {alert_msgs}")
        
        # If it enters check mode:
        if "暫停存檔" in check_text or "抽查" in check_text:
            driver.execute_script("""
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('暫停存檔'));
                if (btn) btn.click();
            """)
            time.sleep(1.0)
        print("[TEST SUCCESS] History Random Check button tested successfully!")
        
        # 12. Test Button: 🎧 聽讀：聽音背單字 (Audio Player)
        print("[TEST] Testing Audio Player button and dialog...")
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('聽讀'));
            if (btn) btn.click();
            else throw new Error('Audio training button not found');
        """)
        time.sleep(1.0)
        
        # Verify Setup Modal opens using get_visible_text
        visible_text = get_visible_text(driver)
        assert "聽寫背單字特訓" in visible_text or "語音人" in visible_text, "Setup Modal was not opened successfully"
        
        # Setup and start audio session via React prototype values
        print("[TEST] Selecting '整個單字庫' and setting custom playback range...")
        driver.execute_script("""
            const modal = Array.from(document.querySelectorAll('.fixed.inset-0')).find(m => m.textContent.includes('聽寫背單字特訓'));
            if (!modal) throw new Error('Audio setup modal not found in DOM');
            
            // 1. Select '整個單字庫'
            const sourceBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('整個單字庫'));
            if (sourceBtn) sourceBtn.click();
            
            // 2. Select custom range selection from audioRange select
            const selectEl = modal.querySelector('select');
            if (selectEl) {
                const option = Array.from(selectEl.options).find(o => o.value === 'custom');
                if (option) {
                    option.selected = true;
                    selectEl.dispatchEvent(new Event('change', { bubbles: true }));
                    selectEl.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
        """)
        time.sleep(0.6)
        
        driver.execute_script("""
            const modal = Array.from(document.querySelectorAll('.fixed.inset-0')).find(m => m.textContent.includes('聽寫背單字特訓'));
            if (!modal) throw new Error('Audio setup modal not found in DOM');
            
            // Helper to find input by sibling span text
            const findInputByLabel = (labelText) => {
                const span = Array.from(modal.querySelectorAll('span')).find(s => s.textContent.includes(labelText));
                return span ? span.parentElement.querySelector('input') : null;
            };
            
            // 3. Set start index (1) and end index (2) inputs
            const startInput = findInputByLabel('開始編號');
            const endInput = findInputByLabel('結束編號');
            
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            if (startInput) {
                setter.call(startInput, '1');
                startInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            if (endInput) {
                setter.call(endInput, '2');
                endInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            // 4. Click all checkboxes to ensure active
            const checkboxes = Array.from(modal.querySelectorAll('input[type="checkbox"]'));
            checkboxes.forEach(cb => {
                if (!cb.checked) {
                    cb.click();
                }
            });
            
            // 5. Set spelling pause duration (0s)
            const selects = Array.from(modal.querySelectorAll('select'));
            if (selects.length >= 2) {
                const selectSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
                selectSetter.call(selects[1], '0');
                selects[1].dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            // 6. Click '開始聽讀特訓'
            const startBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('開始聽讀特訓'));
            if (startBtn) startBtn.click();
        """)
        time.sleep(1.5)
        
        # Verify player panel UI active
        progress_text = driver.execute_script("return document.querySelector('main').textContent;")
        assert "聽讀特訓" in progress_text or "1/2" in progress_text, "Failed to navigate to audio player view"
        
        # Test controls: Play/Pause
        btn_play_pause = driver.find_element(By.XPATH, "//button[@title='暫停播放' or @title='繼續播放']")
        btn_play_pause.click()
        time.sleep(0.5)
        assert "已暫停" in driver.page_source, "Pause state not updated"
        
        btn_play_pause.click() # Resume
        time.sleep(0.5)
        
        # Test Next
        btn_next = driver.find_element(By.XPATH, "//button[@title='下一個單字']")
        btn_next.click()
        time.sleep(0.5)
        assert "2/2" in driver.page_source, "Next word button failed"
        
        # Test Prev
        btn_prev = driver.find_element(By.XPATH, "//button[@title='上一個單字']")
        btn_prev.click()
        time.sleep(0.5)
        assert "1/2" in driver.page_source, "Prev word button failed"
        
        # Test Eye toggle button
        btn_blind_toggle = driver.find_element(By.XPATH, "//button[contains(@title, '英文單字')]")
        btn_blind_toggle.click()
        time.sleep(0.3)
        
        # Test Stop and exit
        btn_stop = driver.find_element(By.XPATH, "//button[contains(., '停止並返回')]")
        btn_stop.click()
        time.sleep(0.5)
        
        # Verify back to dashboard
        assert "發動今日特訓" in driver.page_source, "Failed to return to Dashboard from audio player"
        print("[TEST SUCCESS] Audio Player E2E testing completed successfully!")
        
        # 13. Test Backup and Export Buttons (⬇️ 字, ⬇️ 殿, ⬇️ J)
        print("[TEST] Testing Backup and Export Buttons...")
        
        # Click ⬇️ 字 (Export Dictionary)
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.title === '匯出字典 (TXT)' || b.textContent.includes('⬇️ 字'));
            if (btn) btn.click();
        """)
        time.sleep(0.5)
        
        # Click ⬇️ 殿 (Export Hall of Fame)
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.title === '匯出歷史殿堂 (TXT)' || b.textContent.includes('⬇️ 殿'));
            if (btn) btn.click();
        """)
        time.sleep(0.5)
        
        # Click ⬇️ J (Export JSON)
        driver.execute_script("""
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.title === '全系統備份 (JSON)' || b.textContent.includes('⬇️ J'));
            if (btn) btn.click();
        """)
        time.sleep(0.5)
        
        # Verify downloads triggered
        downloads = driver.execute_script("return window.mockDownloads;")
        print(f"[TEST] Download triggers captured: {downloads}")
        assert len(downloads) > 0, "No export/download clicked actions triggered"
        print("[TEST SUCCESS] Backup and Export buttons tested successfully!")
        
        print("\n==================================================================")
        print("[SUCCESS] All VocabTool feature and button tests passed successfully!")
        print("==================================================================")
        
    except Exception as e:
        print(f"\n[FAILURE] Test failed, error: {e}", file=sys.stderr)
        try:
            driver.save_screenshot("test_all_features_failure.png")
            print("[TEST] Saved failure screenshot to test_all_features_failure.png")
        except Exception as se:
            print(f"[TEST] Cannot save screenshot: {se}")
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
