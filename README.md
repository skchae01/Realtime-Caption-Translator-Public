# Realtime Title Translator

An automated screen translation tool that captures a designated subtitle or text region on your screen, performs text recognition (OCR), and concurrently translates it into multiple target languages in real-time.

---

## ✨ Key Features

* **Multi-engine Parallel Translation**: Calls **Google Translate V3**, **Baidu Translate**, and **DeepL** concurrently using a `ThreadPoolExecutor` to minimize latency.
* **Smart OCR with Auto Fallback**: Leverages **PaddleOCR** for robust text recognition, trying GPU acceleration first and gracefully falling back to CPU modes if needed.
* **Interactive Screen Capture**: Easy visual coordinate selector that allows you to specify the exact subtitle bounding box on your screen.
* **Microsoft Word Dictation Integration**: Automates keypresses to sync the translated text directly into MS Word (useful for logging, subtitle recording, or transcription work).
* **Automatic Currency Conversion**: Automatically detects Chinese Yuan (CNY) pricing patterns in translations and converts them to South Korean Won (KRW) using real-time Yahoo Finance exchange rates.
* **Google Translate Quota Management**: Tracks daily character usage to prevent unexpected API costs and seamlessly falls back to other translators when daily limits are reached.

---

## 📋 Prerequisites

* **Operating System**: Windows (required for screen capturing, DPI awareness, and `win32gui` window activation).
* **Python**: Version 3.10 or newer.

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Realtime-Title-Translator.git
cd Realtime-Title-Translator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Optionally, if you want advanced OCR features, install paddlex via `pip install "paddlex[ocr]"`).*

### 3. Create Configuration (.env) File
Create a file named `.env` in the root of the project folder:
```ini
# DeepL API Authentication Key
DEEPL_AUTH_KEY=your_deepl_api_key_here

# Baidu Translate API Credentials
BAIDU_APP_ID=your_baidu_app_id_here
BAIDU_SECRET_KEY=your_baidu_secret_key_here

# Google Cloud Settings (Optional, uses Application Default Credentials if empty)
GOOGLE_PROJECT_ID=your_google_project_id_here
```

### 4. Run the Tool
```bash
python Realtime-Title-Translator_v1.0.py
```

---

## 🎮 How to Use

1. **Set Up Capture Region**:
   * Follow the console prompts to hover your mouse cursor over the **Top-Left** corner of the subtitle region and press Enter.
   * Move your mouse to the **Bottom-Right** corner of the subtitle region and press Enter.
   * The program will show a red border overlay to confirm your selection.
2. **Main Translation Loop**:
   * The tool continuously captures the selected area and extracts text.
   * If new text is detected, it triggers the parallel translation engine and outputs the results to your terminal.
3. **Interactive Commands**:
   At the end of every loop detection, you can enter commands in the terminal:
   * `enter` (Pressing Enter with no input): Continues to the next scan.
   * `bbb`: Shows the red border overlay around the capture region again (press `ESC` to hide it).
   * `qqq`: Opens the **Google Translate Quota Manager** interface, allowing you to view daily usage statistics, reset limits, or update thresholds.
   * `xxx`: Exits the translator.

---

## 🛠️ Editor Integration (Sublime Text)

If you use Sublime Text, you can run the script directly within the editor using a custom build system.
* See [SUBLIME_TEXT_SETUP.md](SUBLIME_TEXT_SETUP.md) for full instructions on setting up auto-detecting Python virtual environments.

---

## 📝 License

This project is licensed under the MIT License.
