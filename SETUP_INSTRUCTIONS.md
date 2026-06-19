# Setup Instructions for Realtime Title Translator

## Installation Steps

1. **Install basic PaddleOCR (without PaddleX):**
   ```
   pip install paddleocr paddlepaddle
   ```

2. **Install other dependencies:**
   ```
   pip install opencv-python numpy pillow requests
   pip install pypiwin32 urllib3 tqdm clipboard
   pip install google-cloud-storage google-cloud-translate
   pip install pyautogui pywinauto
   pip install pinyin_jyutping_sentence termcolor yfinance colorama
   ```

3. **If you want advanced OCR features (optional):**
   ```
   pip install paddlex
   ```

## Troubleshooting

### Error: "OCR requires additional dependencies"
This means you need to install PaddleX with OCR extras. Try:
```
pip install "paddlex[ocr]"
```

### Error: "use_textline_orientation" not recognized
The code now has fallback initialization that will try multiple methods:
1. use_textline_orientation=True (requires PaddleX)
2. use_angle_cls=True (standard PaddleOCR)
3. Basic initialization
4. Minimal initialization

### Error: Missing other packages
Install them individually:
```
pip install [package_name]
```

## Running the Script
```
python Realtime-Title-Translator_v1.0.py
```
