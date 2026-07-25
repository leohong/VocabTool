# 🧠 極限單字特訓系統 Mobile App - 產品規格書 (Product Specification)

*   **文件版本 (Document Version)**：1.6.2
*   **適用專案 (Target Project)**：`VocabTool-App` (Capacitor Android + React 18 Mobile Version)

本規格書詳細紀錄「極限單字特訓系統 Mobile App」的系統架構、核心演算法、資料儲存結構、特訓功能模組以及組態規範。

---

## 1. 系統架構 (System Architecture)

*   **部署與打包型態**：
    *   **Mobile App**：基於 **Capacitor 7** 的 Android 原生應用程式（包含 `android/` 工程目錄與 `VocabTool-v1.0.apk`）。
    *   **Web App**：離線 Single Page Application (SPA)，所有網頁靜態資源置於 `www/` 目錄中。
*   **前端依賴與技術棧**：
    *   **React 18**：負責模組化 UI 渲染與狀態管理。
    *   **Tailwind CSS**：負責介面樣式排版（Glassmorphism 玻璃質感、極深色科技暗黑風格）。
    *   **Babel (Standalone)**：瀏覽器端即時轉譯。
*   **資料儲存與備份 (Data & Backup)**：
    *   **混合原生持久儲存**：所有的偏好設定使用 `@capacitor/preferences` 儲存，大型字庫與學習進度使用 `@capacitor/filesystem` 寫入 Android/iOS 原生沙盒之 JSON 實體檔案中，保證資料永不因 OS 清理快取而丟失。
    *   **網頁 Fallback 機制**：在 Web 瀏覽器環境中，自動 Promise 封裝降級使用瀏覽器的 `localStorage`，保證雙平台架構完全相容。
    *   **手動 JSON/TXT 備份還原**：提供手動下載 `極限完整備份.json` 系統檔與 `字典/歷史殿堂.txt` 檔案，方便使用者手動進行資料的移轉與備份，100% 離線可用。

---

## 2. 資料庫設計與結構 (Database Design & Schemas)

### 2.1 本地儲存與原生沙盒檔案定義
*   **Preferences 偏好設定 (原生 SharedPreferences/NSUserDefaults 或 Web LocalStorage)**：
    *   `vocab_currentDB`：當前選擇的單字庫名稱（預設為 `vocab_2000`）。
    *   `vocab_dbList`：字庫名稱列表（預設包含 `vocab_2000`, `vocab_7000`）。
    *   `vocab_speechRate`：朗讀語速（預設為 `0.8`）。
    *   `vocab_speechEnabled`：發音開關（預設為 `true`）。
    *   `vocab_audioSettings`：聽寫朗讀參數設定。
*   **Filesystem 原生沙盒檔案 (原生沙盒 Directory.Data 下之實體 JSON 檔，或 Web LocalStorage)**：
    *   `vocab_data_{dbName}.json` (Web 為 `vocab_customVocab_{dbName}`)：存放字庫的單字陣列 (`Word[]`)。
    *   `vocab_state_{dbName}.json` (Web 為 `vocab_state_{dbName}`)：存放字庫的特訓進度天數、錯題本與歷史殿堂數據 (`DBState`)。

### 2.2 單字資料結構 (`Word`)
```typescript
interface Word {
  en: string;       // 英文單字 (去前後空格，保持正確大小寫)
  pos: string;      // 詞性 (如 n., v., adj., adv., prep., idiom 等)
  zh: string;       // 中文釋義
  eg?: string;      // 例句與翻譯提示，格式如 "English sentence. (中文翻譯。)"
}
```

### 2.3 學習狀態資料結構 (`DBState`)
```typescript
interface DBState {
  currentDay: number;                     // 目前特訓天數 (第 1 天起算)
  learnedWords: string[];                 // 已完成學習(封存於歷史殿堂)的英文單字列表
  mistakes: Record<string, number>;       // 當前錯題集，Key 為單字英文，Value 為累積錯誤次數
  historicalMistakes: Record<string, {    // 歷史殿堂單字紀錄
    mistakesCount: number;                // 特訓期間總失誤次數
    nextReviewDate: string;               // 下次幽靈突襲日期 (YYYY-MM-DD)
    intervalStage: number;                // 當前間隔階段 (1: 7天, 2: 21天, 3: 60天, 4: 180天, 5: 永久免疫)
    correctCount?: number;                // 目前在錯題集中的連續拼對次數
    data: Word;                           // 原單字資訊備份
  }>;
  streak: {
    count: number;                        // 連續打卡天數
    lastDate: string | null;              // 上次打卡日期 (YYYY-MM-DD)
  }
}
```

---

## 3. 特訓流水線與核心演算法 (Training Pipeline & Algorithms)

### 3.1 第一階段：快速篩選 (Flashcard Filter)
*   **操作**：系統逐一展示今日新單字與到期幽靈單字，並自動播放美式英語發音。
*   **手勢/按鍵**：
    *   👉 **右滑 (Swipe Right)** 或 **`→` 鍵** ➔ 歸類為「認識」，繼續推進。
    *   👈 **左滑 (Swipe Left)** 或 **`←` 鍵** ➔ 歸類為「不熟」，**立即寫入當前錯題集中營**。

### 3.2 第二階段：強制盲測 (Forced Spelling Test)
*   **規則**：篩選結束後打亂不熟單字，隱藏英文拼寫，僅顯示中文釋義、詞性與底線長度占位符（例如 `_ _ _ _ _`）。
*   **懲罰邏輯**：
    1.  **手滑警告 (Slip Warning)**：本輪首次拼錯時發出震動提示，給予第二次輸入機會。
    2.  **失憶強迫重抄 (Strict Correction)**：第二次拼錯時鎖定輸入框，以亮綠色顯示正確拼寫，**強迫使用者對著正確答案完整抄寫一遍**，且該字答對次數歸零，錯題數 +1。

### 3.3 雙倍消除演算法 (Double Elimination Algorithm)
單字必須在盲測中連續拼對指定次數方可畢業：
$$\text{連續拼對目標次數} = \text{Min}(\text{該字錯誤次數} \times 2, 6)$$

---

## 4. 間隔重複與歷史殿堂 (Spaced Repetition System - SRS)

單字順利消除後進駐歷史殿堂，依以下天數間隔自動安插回未來的每日特訓中進行突襲：
*   **Stage 1**：7 天後抽查
*   **Stage 2**：21 天後抽查
*   **Stage 3**：60 天後抽查
*   **Stage 4**：180 天後抽查
*   **Stage 5 (永久免疫 🛡️)**：通過 180 天抽查後永久封存，不再突襲。

---

## 5. 聽寫背單字特訓播放器 (Audio Dictation Player)

*   **發音管線 (Speech Pipeline)**：`唸英文單字` ➔ `逐字母拼讀 (朗讀速率同步，自訂字母間隔 0~0.5s)` ➔ `唸單字與中文釋義` ➔ `朗讀例句 (自動靜音中文括號內譯文)` ➔ `停頓` ➔ `下一字`。
*   **盲聽模式與動畫**：支援遮蔽單字拼寫與中文，拼讀時伴隨文字放大高亮動畫。
*   **防鎖屏 (Wake Lock)**：調用 `navigator.wakeLock.request('screen')` 防止行動裝置休眠。

---

## 6. Capacitor 與 Android 整合規範

*   **Capacitor 設定檔** (`capacitor.config.json`)：
    ```json
    {
      "appId": "com.vocabtool.app",
      "appName": "極限單字特訓",
      "webDir": "www"
    }
    ```
*   **原生 Android 命令**：
    *   同步網頁靜態資源：`npx cap sync android`
    *   開啟 Android Studio：`npx cap open android`

---

## 7. 程式碼模組化結構與建置程序 (Modular Structure & Build Process)

本專案自 v1.5.0 起，將原先巨大（逾 3300 行）的單一腳本 `app.js` 拆分成高可讀性、職責分明的模組結構：

### 7.1 目錄與依賴關係
1.  **`utils/` (無狀態演算法)**：
    -   `textUtils.js`：文字清洗與遮罩處理 (`cleanApostrophe`, `maskText`, `maskExample`)。
    -   `dictionaryApi.js`：線上字典 API fetch 與 MyMemory 並行翻譯 (`fetchDictionaryData`)。
2.  **`hooks/` (React 業務狀態與生命週期)**：
    -   `useVocabState.js`：單字字典儲存、天數切換與自動儲存。
3.  **`components/` (視覺元件，純 JSX)**：
    -   `Icons.js`：全域 SVG 元件。
    -   `Header.js`、`Dashboard.js`、`Sessions.js`、`AudioPlayer.js`、`Modals.js`。
4.  **`app.js` (進入點與視圖分派)**：
    -   使用上述 Custom Hooks，並依據 `view` 狀態決定分派渲染哪一個元件。

### 7.2 預編譯打包機制 (`scripts/build.js`)
*   **原因**：Android 原生 WebView 因安全性原則不支援 AJAX 本地 JSX/JS 跨檔讀取。
*   **作法**：透過建置腳本將 10 個模組依賴順序（Utilities ➔ Hooks ➔ Components ➔ Entrypoint）進行合併，以 Babel Standalone 形式直接寫入發布用 `www/index.html` 中的單一 `<script>` 標籤中。

---

## 8. 自託管熱更新機制 (Self-Hosted OTA Hot Code Push)

為了提升維護效率、免除每次微調代碼都需要編譯與商店審核的繁瑣流程，本系統整合了 **Capgo (Capacitor-Updater)** 熱更新外掛，採用自託管模式：
*   **開機安全確認 (`notifyAppReady`)**：App 啟動時向原生端發送就緒宣告，以防損壞更新包造成閃退，自動回滾到前一個穩定版本。
*   **異步更新比對 (`checkForUpdates`)**：啟動 3 秒後於背景 fetch 遠端的 `update.json` 版本定義檔，當 `遠端版本 > 本地版本` 時，彈出更新確認對話框，確認後背景下載 ZIP 解壓並自動重啟載入新版。
*   **斷網容錯防護**：網路中斷或連線失敗時，更新機制會默默失敗放行，100% 確保 App 在離線狀態下正常運作。
*   **自動化 OTA 打包工具 (`scripts/zip_www.js`)**：使用 PowerShell 將編譯好的 `www/` 目錄壓縮為 `dist/www.zip`，以便直接作為 GitHub Releases 發行資源。

