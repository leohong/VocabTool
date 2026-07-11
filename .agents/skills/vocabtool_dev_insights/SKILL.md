---
name: vocabtool_dev_insights
description: Best practices, testing guidelines, and troubleshooting instructions for the VocabTool (背單字工具) single page application.
---

# VocabTool Development Lessons & Guidelines

This skill documents critical design, implementation, and testing pitfalls encountered during the development of the VocabTool SPA, along with their solutions. Future development agents must adhere to these guidelines.

---

## 1. Local Development & Port Management
- **Pitfall**: Leftover Python background server instances listening on the same port (e.g., `8001`) cause subsequent connections to drop silently.
- **Guideline**: Before spinning up a development server, verify and terminate conflicting background processes listening on that port.

---

## 2. Windows & Python Unicode Encoding Conflicts
- **Pitfall**: Chinese string literals (like `"發動今日特訓"`) in Python automation scripts can cause `unicodeescape` syntax errors or get garbled due to Windows default non-UTF-8 console encodings (e.g., CP950/Big5).
- **Guidelines**:
  1. **Language-Independent Selectors**: Prefer selecting elements using unique structural attributes (e.g., `//input[@type="text"]` inside modal wrappers, `//input[@spellcheck="false"]` for spelling input) rather than Chinese placeholder matching.
  2. **Browser-Side JavaScript Execution**: For clicking buttons or checking text labels, execute standard JavaScript inside Chrome (`driver.execute_script`). Chrome evaluates JS internally in UTF-8, making it immune to Python environment encoding translation issues:
     ```python
     # Example: Click "新增單字" button robustly
     driver.execute_script("document.querySelectorAll('button').forEach(b => { if(b.textContent.includes('新增單字')) b.click(); })")
     ```
  3. **Unicode Escapes in Python**: If Chinese literals must be included in Python, use unicode escape sequences (e.g., `\u56de\u5230\u6307\u63ee\u4e2d\u5fc3` for "回到指揮中心") to prevent encoding translation errors in the interpreter.

---

## 3. Selenium Headless Chrome LocalStorage Restrictions
- **Pitfall**: Headless Chrome throws `Access is denied` or storage violations if you execute JS storage writes (`localStorage.setItem`) before navigating to a valid domain.
- **Guideline**: Navigate to the target page first (loading the domain context), execute the `localStorage` setup script, and then refresh (`driver.refresh()`) to apply the mocked state.

---

## 4. Spelling Variant & Suffix Masking (Hint Mode)
- **Pitfall**: Target words in example sentences sometimes have spelling variations (e.g., target `acknowledgement` vs example `acknowledgment`) or suffix changes (e.g., target `judge` vs example `judgment` or plural `judgments`). Simple exact match RegExp masking leaks answers.
- **Guideline**: Implement targeted regex variations for stems with common variations to mask both forms:
  ```javascript
  // Example for spelling variant compatibility masking
  if (w.toLowerCase().includes('acknowledg')) {
    maskedEn = maskedEn.replace(/\backnowledg(e)?ment(s)?\b/gi, '______');
  } else if (w.toLowerCase().includes('judg')) {
    maskedEn = maskedEn.replace(/\bjudg(e)?ment(s)?\b/gi, '______');
  }
  ```

---

## 5. Quiz State & Summary Page Transitions in E2E Testing
- **Pitfall**: If a quiz queue contains only one target word, completing it immediately transitions the React view from `'spelling'` to `'summary'`. Test steps that blindly assert the presence of control buttons like "暫停存檔" on quiz completion will timeout and fail.
- **Guideline**: E2E test scripts must verify the `'summary'` page view text ("特訓完美結束！") and click the "回到指揮中心" return route when the active training queue is exhausted.

---

## 6. Mobile & Tablet Virtual Keyboard Obscuration
- **Pitfall**: Mobile pop-up keyboards consume up to 50% of the vertical viewport. Standard `100vh` layouts don't shrink, pushing card input elements and action buttons off-screen.
- **Guideline (UI Compression)**: Use a React state (`isInputFocused`) to track when spelling inputs are active. Under focus:
  1. Hide non-essential layout items (like `<header>`) using conditional rendering: `{!(view === 'spelling' && isInputFocused) && <header>...</header>}`.
  2. Dynamically reduce card margins and paddings (e.g., `p-4 mb-2` instead of `p-8 mb-6`) to compress the vertical footprint, ensuring the entire card fits inside the remaining vertical space.
