# 📐 極限單字特訓系統 - 系統規格書 (System Specification)

> 本文件為 **VocabTool (背單字工具)** 之架構設計、資料結構、特訓演算法與介面互動規範標準。

---

## 1. 系統概述與設計哲學 (Overview & Philosophy)

VocabTool 專為高強度的長期單字記憶計畫設計，採用 **雙階段流水線 (Flashcard Filter + Forced Spelling Test)** 結合 **雙倍消除演算法** 與 **間隔重複幽靈突襲 (Spaced Repetition Ghost Raids)**。

### 核心原則：
1. **主動回想與強迫盲測**：不提供選擇題輔助，逼迫腦肌神經建立英文與中文之間的直接反射鏈。
2. **手滑警告與記憶斷裂懲罰**：首拼錯誤給予警告震動；二次拼錯視為失憶，鎖定輸入框並強迫完整重抄正確答案。
3. **安全防護與備份機制**：所有進度與字庫皆保存在瀏覽器 `localStorage`，提供雲端直載、TXT 與 JSON 極限還原。

---

## 2. 資料結構與存取規範 (Data Structures & Storage)

### 2.1 全域版本號控制 (Versioning System)
- 常數定義：`APP_VERSION = "X.Y.Z"`（三碼語意化版本號）。
- `X`：Major 主版本、`Y`：Minor 功能版本、`Z`：Git Push/Build 計數。
- UI 展示：僅呈現前兩碼 `X.Y`（例如 `v1.4`），自動截取 `DISPLAY_VERSION`。

### 2.2 單字模型 (Word Model)
```typescript
interface Word {
  en: string;   // 英文單字 (例: "system")
  zh: string;   // 中文釋義 (例: "系統")
  pos: string;  // 詞性 (例: "n.", "v.", "adj.")
  eg?: string;  // 例句 (可選, 例: "A computer system is complex. (電腦系統很複雜。)")
}
```

### 2.3 學習狀態模型 (Learning State Schema)
儲存於 `localStorage` 的 `vocab_state_[dbName]`：

```typescript
interface DatabaseState {
  currentDay: number;                     // 目前特訓天數 (天數從 1 開始)
  mistakes: Array<{                       // 當前錯題集中營
    word: Word;
    wrongCount: number;
    correctCount: number;
  }>;
  history: Array<{                        // 歷史殿堂 (封存單字)
    word: Word;
    wrongCount: number;
    nextReviewDay: number;
    immunized?: boolean;                  // 是否達到永久免疫
  }>;
  streak: {
    count: number;                        // 連續打卡天數
    lastDate: string | null;              // 上次打卡日期 (YYYY-MM-DD)
  }
}
```

### 2.4 檔案匯入/匯出與選單介面規範 (Import & Export Spec)

#### A. 選擇匯入來源選單 (`ImportOptionsModal`)
點擊儀表板 `⬆️ 字` 按鈕觸發彈出 Modal，提供 3 種載入管道：
1. **🎒 載入內建 2000 單字庫**：
   - 優先調用 `fetch('https://raw.githubusercontent.com/leohong/VocabTool/main/2000_%E5%96%AE%E5%AD%97%E5%BA%AB.txt')` 異步載入。
   - 解析內容並提示確認後覆寫目前字庫。
2. **🎓 載入內建 7000 單字庫**：
   - 優先調用 `fetch('https://raw.githubusercontent.com/leohong/VocabTool/main/7000_%E5%96%AE%E5%AD%97%E5%BA%AB.txt')` 異步載入。
3. **📁 從本機選擇檔案 (.txt)**：
   - 觸發隱藏的 `<input type="file" accept=".txt" />`，由使用者選取本地 TXT 單字檔。

> [!NOTE]
> **離線與網路備援邏輯**：當 GitHub 雲端直載遭遇 404 或連線失敗（例如處於離線狀態）時，系統會自動跳出提示並自動切換轉接開啟本機檔案選取器。

#### B. 檔案格式規格
* **字典 TXT 格式**：標頭為 `=== 特訓完整字庫 ===`，單字列格式為 `編號. [詞性] 英文 --> 中文 || 例句`。
* **歷史殿堂 TXT 格式**：標頭為 `=== 歷史殿堂單字個人紀錄 ===`，格式為 `編號. 錯誤次數: X次 | [詞性] 英文 --> 中文`。
* **JSON 全匯入/匯出**：
  - 相容純單字陣列：`[{ en, pos, zh, eg }]`（可替代為 `word`/`meaning`/`example`）。
  - 極限完整備份 (v2.0 `full_system`)：包含 `allDatabases` 物件、全域設定、每日學習目標與打卡紀錄。

---

## 3. 特訓流水線與核心演算法 (Training Pipeline & Algorithms)

### 3.1 第一階段：快速篩選 (Flashcard Filter)
* **展示**：顯示今日新單字與到期幽靈字，並透過 TTS 朗讀發音。
* **判定**：
  * 認識 ➔ 按 `→` 鍵 / 右滑 ➔ 進入下一字。
  * 不認識 ➔ 按 `←` 鍵 / 左滑 ➔ 寫入「當前錯題集中營」。

### 3.2 第二階段：強制盲測 (Forced Spelling Test)
* **規則**：隱藏英文單字，僅展示中文釋義與詞性，游標強制聚焦輸入框。
* **機制**：
  1. **手滑警告 (Slip Warning)**：首拼錯誤觸發警告震動並清空輸入框，給予第二次拼寫機會。
  2. **強迫重抄懲罰 (Strict Correction)**：二次拼錯鎖定輸入框，亮綠色展示正確拼音，強迫使用者對照輸入正確答案方可通過。該字寫入錯題集中營且失誤數 +1。

### 3.3 雙倍消除演算法 (Double Elimination Algorithm)
單字必須在盲測中連續拼對指定次數（通常為 2 次），方可自當前錯題集中清除並移入「歷史殿堂」。

---

## 4. 系統測試與品質規範 (Testing Guidelines)

- **自動化測試工具**：Python + Selenium Headless Chrome。
- **測試執行準則**：
  - **精準局部測試**：優先針對修改模組執行專屬腳本（如 `python test/test_import_options_modal.py`）。
  - **禁止 DOM 控制台輸出**：除錯資訊必須寫入 `test/failure_source.html` 或 `.png` 截圖，禁止 `print(driver.page_source)` 浪費 Token。
