import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
        driver.get(file_url)
        
        # 2. Setup mock vocabulary database in localStorage (3 words)
        mock_setup_script = """
        localStorage.clear();
        localStorage.setItem('vocab_currentDB', 'vocab_test');
        localStorage.setItem('vocab_customVocab_vocab_test', JSON.stringify([
            { en: 'apple', zh: 'n. 蘋果', pos: 'n.', eg: 'This is an apple.' },
            { en: 'banana', zh: 'n. 香蕉', pos: 'n.', eg: 'I love bananas.' },
            { en: 'orange', zh: 'n. 柳橙', pos: 'n.', eg: 'Orange juice is delicious.' }
        ]));
        localStorage.setItem('vocab_state_vocab_test', JSON.stringify({
            currentDay: 1,
            learnedWords: [],
            mistakes: {},
            historicalMistakes: {},
            streak: { count: 0, lastDate: null }
        }));
        localStorage.setItem('vocab_wordsPerDay_vocab_test', '3');
        localStorage.setItem('vocab_ghostsPerDay_vocab_test', '0');
        """
        driver.execute_script(mock_setup_script)
        
        # Refresh to apply local storage
        driver.refresh()
        time.sleep(1) # wait for render
        
        # 3. Inject Mock speechSynthesis & confirm overrides
        mock_speech_script = """
        window.confirm = () => true;
        window.speechSynthesis.getVoices = () => [
            { name: 'Google US English', lang: 'en-US', default: true }
        ];
        window.speechSynthesis.speak = (utterance) => {
            setTimeout(() => {
                if (utterance.onend) utterance.onend();
            }, 30);
        };
        window.speechSynthesis.cancel = () => {};
        """
        driver.execute_script(mock_speech_script)
        
        # 4. Click start daily session button
        wait = WebDriverWait(driver, 5)
        # Find button with text "發動今日特訓" using JS to avoid console encoding issues
        driver.execute_script("""
            const btns = Array.from(document.querySelectorAll('button'));
            const startBtn = btns.find(b => b.textContent.includes('發動今日特訓'));
            if (startBtn) startBtn.click();
            else throw new Error('Could not find start button');
        """)
        
        # 5. Wait for scanning view to load
        time.sleep(1)
        
        # Check current word
        first_word = driver.execute_script("return document.querySelector('h2').textContent;")
        
        # 6. Delete this word
        driver.execute_script("""
            const deleteBtn = document.querySelector('button[title="徹底刪除此單字"]');
            if (deleteBtn) deleteBtn.click();
            else throw new Error('Could not find delete button');
        """)
        time.sleep(1)
        
        # Verify word changed
        second_word = driver.execute_script("return document.querySelector('h2').textContent;")
        assert first_word != second_word, f"Failed to skip deleted word: {first_word} is still shown!"
        
        # 7. Complete scanning phase for the remaining 2 words by clicking "認識 (右滑)"
        for i in range(2):
            word_now = driver.execute_script("return document.querySelector('h2').textContent;")
            assert word_now != first_word, f"Deleted word {first_word} appeared in scanning queue again!"
            driver.execute_script("""
                const btns = Array.from(document.querySelectorAll('button'));
                const okBtn = btns.find(b => b.textContent.includes('認識'));
                if (okBtn) okBtn.click();
                else throw new Error('Could not find ok button');
            """)
            time.sleep(0.5)
            
        # 8. Should now be in the spelling stage
        time.sleep(1)
        current_view = driver.execute_script("return document.querySelector('.text-slate-400').textContent;")
        assert "第二關：拼字特訓" in current_view or "拼字" in current_view or "第一關：快速篩選" not in current_view, "Not in spelling phase!"
        
        # 9. Verify that the deleted word does not appear in spelling phase
        spelling_words_seen = []
        for i in range(2):
            spelling_word = driver.execute_script("return document.querySelector('h2').textContent;")
            assert spelling_word != first_word, f"FAILED: Deleted word {first_word} appeared in Spelling stage!"
            spelling_words_seen.append(spelling_word)
            # Submit spelling (simulate typing and submitting correctly or skipping)
            # We can force correct spelling input
            driver.execute_script(f"""
                const input = document.querySelector('input[type="text"]');
                if (input) {{
                    input.value = '{spelling_word}';
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            """)
            # Press enter
            driver.execute_script("""
                const input = document.querySelector('input[type="text"]');
                if (input) {
                    const e = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true });
                    input.dispatchEvent(e);
                }
            """)
            time.sleep(0.5)
            
        print("[SUCCESS] test_delete_word passed.")
        
    except Exception as e:
        print(f"[TEST FAILED] Error: {e}", file=sys.stderr)
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Save screenshot
            screenshot_path = os.path.join(current_dir, "test_delete_word_failure.png")
            driver.save_screenshot(screenshot_path)
            print(f"[TEST] Saved screenshot to {screenshot_path}", file=sys.stderr)
            
            # Save page source to local file
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
