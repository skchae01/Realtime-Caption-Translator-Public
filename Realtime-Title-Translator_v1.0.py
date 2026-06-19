# -*- Encoding: utf-8 -*-
# => To run this program, press (F5) in SublimeText3 editor
# cspell:words pyautogui pywinauto paddleocr paddlex paddlepaddle opencv pinyin jyutping termcolor colorama pypiwin32 appid secretkey baidu fanyi textline minjin
# pip install pypiwin32
# pip install urllib3
# pip install tqdm
# pip install clipboard
# pip install google-cloud-storage
# pip install google-cloud-translate
# pip install pyautogui pywinauto  # cspell:disable-line
# pip install "paddlex[ocr]"  # cspell:disable-line
# pip install paddleocr paddlepaddle  # cspell:disable-line
# pip install opencv-python
# pip install pinyin_jyutping_sentence
# pip install termcolor
# pip install yfinance

import requests
import http.client, hashlib, urllib, random, json #, string
import os, sys, platform, time # noqa: E401
from pathlib import Path
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import clipboard
import win32gui, win32ui, win32api, win32con
from win32api import GetSystemMetrics
# Translation API V3 (google-cloud-translate SDK) - replaces the v2 REST + API key path
from google.cloud import translate_v3 as translate
from google.api_core import client_options
from google.api_core.exceptions import ResourceExhausted, PermissionDenied, ServiceUnavailable, DeadlineExceeded
from PIL import ImageGrab  # ImageFile  # from PIL import Image
# import pytesseract
from paddleocr import PaddleOCR  # cspell:disable-line
from ctypes import windll
import cv2
import numpy as np
import subprocess
import re
from pinyin_jyutping_sentence import pinyin  # cspell:disable-line
from termcolor import colored
from colorama import init
import pyautogui  # cspell:disable-line
import pywinauto  # cspell:disable-line
init()

print("*** platform.python_version() => ", platform.python_version())
# print("*** current working Directory => ", os.getcwd())
print("*** current working Directory => ", Path.cwd())
print("*** my current python script ==> ", sys.argv[0])


# =================== Initialize PaddleOCR =================== #
# This is done early to front-load the model loading time.
try:
    # Try the newer initialization first with GPU
    ocr = PaddleOCR(use_textline_orientation=True, use_gpu=True)
    print("PaddleOCR initialized successfully with use_textline_orientation=True (GPU enabled)")
except Exception as e:
    print(f"Error initializing PaddleOCR with use_textline_orientation (GPU): {e}")
    print("Trying alternative initialization...")
    try:
        # Fallback to standard CPU mode without specifying use_gpu
        ocr = PaddleOCR(use_textline_orientation=True)
        print("PaddleOCR initialized successfully with use_textline_orientation=True")
    except Exception as e_cpu:
        print(f"Error with use_textline_orientation: {e_cpu}")
        try:
            # Fallback to the older, more compatible initialization
            ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            print("PaddleOCR initialized with use_angle_cls=True")
        except Exception as e2:
            print(f"Error with use_angle_cls: {e2}")
            try:
                # Most basic initialization without PaddleX dependencies
                ocr = PaddleOCR(lang='ch')
                print("PaddleOCR initialized with basic settings")
            except Exception as e3:
                print(f"Failed to initialize PaddleOCR with basic settings: {e3}")
                print("Trying the most minimal initialization...")
                try:
                    # Absolute minimal initialization
                    from paddleocr import PaddleOCR as BasePaddleOCR
                    ocr = BasePaddleOCR()
                    print("PaddleOCR initialized with minimal settings")
                except Exception as e4:
                    print(f"Failed to initialize PaddleOCR: {e4}")
                    print("Please install the required dependencies:")
                    print("pip install paddleocr paddlepaddle")
                    print("If the error persists, try: pip install paddlex")
                    sys.exit(1)

# 언어 설정
sourceLanguage = 'chi_sim' #=> 중국어 간체
# sourceLanguage = 'spa' #=> 스페인어
# sourceLanguage = 'ita' #=> 이탈리아어
# sourceLanguage = 'eng'  #=> 영어

# =================== Google Translate Quota Management =================== #
# Global quota tracking variables
google_quota_exhausted = False
google_last_quota_check = 0
google_quota_reset_time = 24 * 60 * 60  # 24 hours in seconds
daily_character_count = 0
daily_character_limit = 500000  # Adjust based on your actual quota limit
quota_warning_threshold = 0.9  # Warn at 90% of quota

def save_quota_status():
    """Save quota status to file for persistence across restarts"""
    quota_data = {
        'quota_exhausted': google_quota_exhausted,
        'last_check': google_last_quota_check,
        'daily_count': daily_character_count,
        'date': time.strftime('%Y-%m-%d')
    }
    try:
        with open('google_quota_status.json', 'w', encoding='utf-8') as f:
            json.dump(quota_data, f)
    except Exception as e:
        print(f"Warning: Could not save quota status: {e}")

def load_quota_status():
    """Load quota status from file"""
    global google_quota_exhausted, google_last_quota_check, daily_character_count
    try:
        with open('google_quota_status.json', 'r', encoding='utf-8') as f:
            quota_data = json.load(f)
        
        # Check if it's a new day
        today = time.strftime('%Y-%m-%d')
        if quota_data.get('date') != today:
            # New day - reset counters
            daily_character_count = 0
            google_quota_exhausted = False
            print(f"*** New day detected - Google Translate quota reset")
        else:
            # Same day - restore saved status
            google_quota_exhausted = quota_data.get('quota_exhausted', False)
            google_last_quota_check = quota_data.get('last_check', 0)
            daily_character_count = quota_data.get('daily_count', 0)
            
            if google_quota_exhausted:
                print(colored("*** Google Translate quota exhausted (from previous session)", 'yellow'))
            elif daily_character_count > 0:
                percent_used = (daily_character_count / daily_character_limit) * 100
                print(f"*** Google Translate usage today: {daily_character_count:,} characters ({percent_used:.1f}%)")
                
    except (FileNotFoundError, json.JSONDecodeError):
        # File doesn't exist or is corrupted - start fresh
        daily_character_count = 0
        google_quota_exhausted = False
        print("*** Starting fresh Google Translate quota tracking")

# Load quota status on startup
load_quota_status()

# Load environment variables from a local .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 百度通用翻译API,不包含词典、tts语音合成等资源，如有相关需求请联系translate_api@baidu.com
# Settings for Baidu  
appid = os.getenv('BAIDU_APP_ID', '20210210000695427')
secretKey = os.getenv('BAIDU_SECRET_KEY', 'wS6KbtnywH22bs0VD_at')
httpClient = None
myurl = '/api/trans/vip/translate'
fromLang = 'auto'   # 原文语种  # fromLang = 'zh'
toLang = 'kor'   # 译文语종
salt = random.randint(32768, 65536)

# =================== OneDrive path 설정 =================== # 
# auto detect OneDrive folder (optional fallback)
user_profile_path = os.getenv('USERPROFILE')
onedrive_folder = 'OneDrive'
onedrive_path = os.getenv('ONEDRIVE_PATH')
if not onedrive_path and user_profile_path:
    onedrive_path = os.path.join(user_profile_path, onedrive_folder)
    if platform.node() in ["Steven-Dell","steven-samsung"]:
        onedrive_path = r'D:\OneDrive'

if onedrive_path and os.path.exists(onedrive_path):
    print(f'{onedrive_path=}')

# Use relative path by default, fallback to absolute user paths if specified in env
script_dir = Path(__file__).resolve().parent
gitHub_folder = os.getenv('GITHUB_FOLDER')
if not gitHub_folder:
    gitHub_folder = str(script_dir / 'KoreanNumber')

if not os.path.exists(gitHub_folder):
    print(f"gitHub folder not found at '{gitHub_folder}'. Please check config.")
    exit()
sys.path.append(gitHub_folder)

# Settings for Google Cloud and dictation 
dictation_file_path = os.getenv('DICTATION_FILE_PATH')
if not dictation_file_path:
    dictation_file_path = str(script_dir / 'dotx' / 'steven2.dotx')

# Google Cloud Translation API V3 (SDK + ADC)
# Auth: uses Application Default Credentials. Run once in this environment:
#   gcloud auth application-default login
# (or set GOOGLE_APPLICATION_CREDENTIALS to a service-account key file).
PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID', 'coastal-gantry-167112')
LOCATION = "us-central1"
_translate_options = client_options.ClientOptions(quota_project_id=PROJECT_ID)
translate_client = translate.TranslationServiceClient(client_options=_translate_options)
PARENT = f"projects/{PROJECT_ID}/locations/{LOCATION}"
# Retired: v2 REST API key (no longer used now that we call the V3 SDK)
# API_KEY = "AIzaSyAkQXZaOl_NCoRLWc4LeG21c6lmtogusu0"
# Comment out service account credentials - now using API key instead
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = user_profile_path + r"\GoogleCloudPlatform-steven-e4bac841ed64.json"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\PC\myCoding\GoogleCloudPlatform-steven-e4bac841ed64.json"
if platform.node() == 'Dell-XPS-Steven':  # eBroadcast 사무실 PC
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\steven\GoogleCloudPlatform-steven-e4bac841ed64.json"
    # dictation_file_path = 'C:\\Users\\skcha\\OneDrive\\steven1.dotx'
    # dictation_file_path = 'C:\\Users\\skcha\\OneDrive\\dotx\\steven2.dotx'
    args = ['C:\\Program Files\\Microsoft Office\\root\\Office16\\winword.exe', dictation_file_path]
elif platform.node() == "Galaxy-Steven":  #  steven's Galaxy pc 
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\steven\GoogleCloudPlatform-steven-e4bac841ed64.json"  # noqa: E501
    # sys.path.append(r'C:\Users\skcha\OneDrive\Documents\GitHub\KoreanNumber')
    args = ['C:\\Program Files\\Microsoft Office\\root\\Office16\\winword.exe', dictation_file_path]
elif platform.node() == "PC_minjin":  #  minjin's Dell pc Inspiron 3020 S
    args = ['C:\\Program Files\\Microsoft Office\\root\\Office16\\winword.exe', dictation_file_path]
elif platform.node() == "Steven-Dell":  #  Steven-Dell Inspiron  15 7559 서비스 태그: DG0ZKD2
    args = ['C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\winword.exe', dictation_file_path]
elif platform.node() == "steven-samsung":  #  steven's Samsung NoteBook - System Model: 550XCJ/550XCR
    args = ['C:\\Program Files\\Microsoft Office\\root\\Office16\\winword.exe', dictation_file_path]
elif platform.node() == "Dell-3070":  #  steven's Dell-3070 PC 
    args = ['C:\\Program Files\\Microsoft Office\\root\\Office16\\winword.exe', dictation_file_path]
else:  # or others
    print("*** 주의:: 현재 사용중인 컴퓨터는 등록되지 않았습니다!! platform.node() => ", platform.node())

# import kr2num   ## Korean -> Number
import checkYuan_py_v2   ## checkYuan -> checkYuan_RT 
CNY_KRW_RT = 0

subprocess.Popen(args, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
print("*** waiting for MS word open!! ")

dictation_flag = True
dictation_file_process = "steven2.dotx - Word"
# dictation_file_process = "steven1-PC_minjin.dotx - Word"
takeTooLong_cnt = 0
print("Attempting to find and activate MS Word window...")
w = None 
while takeTooLong_cnt < 20:  # Timeout after ~20 seconds
    try:
        windows = pyautogui.getWindowsWithTitle(dictation_file_process)
        if windows:
            w = windows[0]
            print(f"Found window: {w.title} (Handle: {w._hWnd})")
            w.activate()
            print("Window activated successfully.")
            pyautogui.hotkey('alt', '`')
            break  # Success
        else:
            print(f"Word window not found yet, attempt {takeTooLong_cnt + 1}/20...", end='\r')
            time.sleep(1)
    except Exception as e:
        print(f"\nAn error occurred while trying to find/activate Word: {e}")
        time.sleep(3)

    takeTooLong_cnt += 1

if not w:
    print("\nCould not find or activate MS Word window.")
    if input("Proceed without Word dictation? (y/n): ").lower() == 'y':
        dictation_flag = False
    else:
        print("Exiting script as Word dictation is required.")
        sys.exit()

# DPI 인식 설정으로 정확한 커서 위치 획득
try:
    windll.shcore.SetProcessDpiAwareness(1)
except Exception as e:
    print("경고: DPI 인식 설정 실패 -", e)

def get_user_coordinates():
    """사용자로부터 좌상단 및 우하단 좌표 입력 받기"""
    while True:
        input("1. 좌상단 모서리에 마우스를 위치시키고 엔터키를 누르세요...")
        x1, y1 = win32gui.GetCursorPos()
        input("2. 우하단 모서리에 마우스를 위치시키고 엔터키를 누르세요...")
        x2, y2 = win32gui.GetCursorPos()

        # 좌표 정렬 (x1 < x2, y1 < y2)
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        print(f"\n선택 영역: 좌상단({x1}, {y1}), 우하단({x2}, {y2})")
        
        # 사용자 확인
        if input("영역을 재설정하려면 'set' 입력, 계속하려면 엔터키: ").lower() != 'set':
            break
    return x1, y1, x2, y2

USER_COORDINATES_FILE = "user_coordinates.md"

def save_user_coordinates(x1, y1, x2, y2, filepath=USER_COORDINATES_FILE):
    """사용자가 정의한 캡처 영역 좌표를 마크다운 파일로 저장.
    저장 형식 예:
        # Capture Region Coordinates
        - x1: 100
        - y1: 200
        - x2: 300
        - y2: 400
    """
    content = (
        "# Capture Region Coordinates\n"
        f"\n"
        f"- x1: {x1}\n"
        f"- y1: {y1}\n"
        f"- x2: {x2}\n"
        f"- y2: {y2}\n"
    )
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"*** 좌표가 '{filepath}' 파일에 저장되었습니다.")
    except Exception as e:
        print(f"*** 경고: 좌표 저장 실패 - {e}")


def show_red_border_overlay(x1, y1, x2, y2, duration=3, border_width=4):
    """
    빨간색 테두리 오버레이 창을 PyQt5로 표시합니다.
    x1, y1, x2, y2: 화면 좌상단/우하단 좌표
    duration: 표시 시간(초)
    border_width: 테두리 두께(픽셀)
    """
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import Qt, QTimer, QRect
    from PyQt5.QtGui import QPainter, QPen

    class BorderOverlay(QWidget):
        def __init__(self, x1, y1, x2, y2, border_width, duration):
            super().__init__()
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setGeometry(x1, y1, x2 - x1, y2 - y1)
            self.border_width = border_width
            QTimer.singleShot(int(duration * 1000), self.close)

        def paintEvent(self, event):
            painter = QPainter(self)
            pen = QPen(Qt.red, self.border_width)
            painter.setPen(pen)
            rect = QRect(0, 0, self.width()-1, self.height()-1)
            painter.drawRect(rect)

    app = QApplication.instance() or QApplication(sys.argv)
    overlay = BorderOverlay(x1, y1, x2, y2, border_width, duration)
    overlay.show()
    # If running inside an existing QApplication, process events for duration
    if QApplication.instance():
        end_time = time.time() + duration
        while time.time() < end_time:
            app.processEvents()
        overlay.close()
    else:
        app.exec_()

# 사용 예시:
# show_red_border_overlay(x1, y1, x2, y2, duration=3)


def show_red_border_until_esc(x1, y1, x2, y2, border_width=4):
    """
    빨간색 테두리 오버레이를 ESC 키가 눌릴 때까지 계속 표시.
    오버레이는 입력을 받지 않으므로(WindowTransparentForInput),
    ESC 키 감지는 win32api.GetAsyncKeyState 로 전역 폴링한다.
    (Get_coordi_Show_red_overlay_v3.py 의 show_red_border_until_esc 기반)
    """
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget
    from PyQt5.QtCore import Qt, QRect
    from PyQt5.QtGui import QPainter, QPen

    class BorderOverlayEsc(QWidget):
        """ESC 키를 누를 때까지 빨간 테두리만 표시하는 투명 오버레이"""
        def __init__(self, x1, y1, x2, y2, border_width=4):
            super().__init__()
            self.setWindowFlags(
                Qt.FramelessWindowHint
                | Qt.WindowStaysOnTopHint
                | Qt.Tool
                | Qt.WindowTransparentForInput  # 클릭을 아래 창으로 전달
            )
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_ShowWithoutActivating)
            self.setGeometry(x1, y1, x2 - x1, y2 - y1)
            self.border_width = border_width

        def paintEvent(self, event):
            painter = QPainter(self)
            pen = QPen(Qt.red, self.border_width)
            painter.setPen(pen)
            rect = QRect(0, 0, self.width() - 1, self.height() - 1)
            painter.drawRect(rect)

    app = QApplication.instance() or QApplication(sys.argv)
    overlay = BorderOverlayEsc(x1, y1, x2, y2, border_width)
    overlay.show()

    print("\n빨간색 테두리 오버레이를 표시 중입니다. ESC 키를 누르면 종료합니다.")

    # GetAsyncKeyState 의 high-order bit 가 켜져 있으면 현재 키가 눌린 상태
    try:
        while True:
            app.processEvents()
            if win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000:
                break
            time.sleep(0.02)  # CPU 사용 절감
    finally:
        overlay.close()
        app.processEvents()

    print("ESC 키 감지 - 오버레이를 닫았습니다.")

print("===== 자막 캡처 영역 설정 도구 =====")
x1, y1, x2, y2 = get_user_coordinates()
save_user_coordinates(x1, y1, x2, y2)
print("3초 동안 선택 영역을 빨간색 테두리로 표시합니다...")
# draw_red_border(x1, y1, x2, y2)
show_red_border_overlay(x1, y1, x2, y2)
print("\n최종 설정 좌표:")
print(f"좌상단: ({x1}, {y1})")
print(f"우하단: ({x2}, {y2})")
# draw_red_border(x1, y1, x2, y2)
show_red_border_overlay(x1, y1, x2, y2)

# 특정언어로된 문자가 몇개 있는지 계산 하기 
# => 중국어 유니코드 범위: [\u4e00-\u9fff] 
# => Most Latinic alphabets: "\u0080" to "\u07FF"    
def chars_count(str):
    return sum(
        sourceLanguage == "chi_sim"
        and '\u4e00' <= s <= '\u9fef'
        or sourceLanguage != "chi_sim"
        and '\u0000' <= s <= '\u07FF'
        for s in str
    )

# =================== Translation Helper Functions (Parallelized) =================== #

def translate_baidu(text):
    global appid, secretKey, salt, fromLang, toLang
    # if '习近平', replace it with '蔡先生' => 바이두가 번역안하므로..  
    q1 = re.sub(r'习近平', r'蔡先生', text)  
    sign = appid + q1 + str(salt) + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    path = '/api/trans/vip/translate?appid=' + appid + '&q=' + urllib.parse.quote(q1) \
        + '&from=' + fromLang + '&to=' + toLang \
        + '&salt=' + str(salt) + '&sign=' + sign
    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com', timeout=5)
        httpClient.request('GET', path)
        response = httpClient.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)
        if 'trans_result' in result and len(result['trans_result']) > 0:
            return result['trans_result'][0]['dst']
        else:
            return f"Error: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if 'httpClient' in locals() and httpClient:
            httpClient.close()

def check_quota_status():
    """Check if we should attempt Google Translate based on quota status"""
    global google_quota_exhausted, google_last_quota_check, daily_character_count
    current_time = time.time()
    
    # Reset quota status if enough time has passed (24 hours) or it's a new day
    today = time.strftime('%Y-%m-%d')
    try:
        with open('google_quota_status.json', 'r', encoding='utf-8') as f:
            quota_data = json.load(f)
        if quota_data.get('date') != today:
            google_quota_exhausted = False
            daily_character_count = 0
            print("*** Google Translate quota reset for new day")
    except:
        pass
        
    if google_quota_exhausted and (current_time - google_last_quota_check) > google_quota_reset_time:
        google_quota_exhausted = False
        daily_character_count = 0
        google_last_quota_check = current_time
        print("*** Google Translate quota status reset - attempting to use service again")
    
    # Check if we're approaching the character limit
    if daily_character_count >= daily_character_limit:
        google_quota_exhausted = True
        print(colored("*** Daily character limit reached - disabling Google Translate", 'red'))
        return False
        
    return not google_quota_exhausted

def translate_google(text, max_retries=3):
    """
    Enhanced Google Translate function with quota handling, retries, and fallback.
    Uses Google Cloud Translation API V3 (google-cloud-translate SDK) with ADC.
    """
    global google_quota_exhausted, google_last_quota_check, daily_character_count
    
    # Check character count before attempting translation
    text_length = len(text)
    if daily_character_count + text_length > daily_character_limit:
        return f"Error: Character limit would be exceeded ({daily_character_count + text_length:,} chars)"
    
    # Skip Google Translate if quota is exhausted
    if not check_quota_status():
        return "Error: QUOTA EXHAUSTED - Skipping Google Translate"
    
    # Language code mapping
    language_map = {
        "chi_sim": "zh-CN",
        "eng": "en",
        "ita": "it", 
        "spa": "es"
    }
    
    source_language_code = language_map.get(sourceLanguage, "ko")
    if sourceLanguage not in language_map:
        print("*** [구글] 원하는 언어가 설정되지 않았습니다!! ")

    # API V3 request
    request_params = {
        "parent": PARENT,
        "contents": [text],
        "mime_type": "text/plain",
        "source_language_code": source_language_code,
        "target_language_code": "ko",
    }

    # Try translation with exponential backoff
    for attempt in range(max_retries):
        try:
            response = translate_client.translate_text(request=request_params)
            trText = response.translations[0].translated_text
            trText = re.sub(r'​', '', trText)  # Remove zero-width spaces

            # Success - update character count
            daily_character_count += text_length
            save_quota_status()  # Save updated status
            return trText

        except ResourceExhausted as e:
            msg = str(e).lower()
            is_daily_limit = any(kw in msg for kw in (
                "daily limit", "quota", "limit exceeded", "resource_exhausted",
            ))
            if is_daily_limit:
                google_quota_exhausted = True
                google_last_quota_check = time.time()
                save_quota_status()
                print(colored("Google==> QUOTA EXHAUSTED! Quota exceeded for today.", 'red', 'on_yellow'))
                return f"Error: Quota exceeded - {msg}"
            # Transient rate-limit burst
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                return f"Error: Rate limited after all retries"

        except PermissionDenied as e:
            google_quota_exhausted = True
            google_last_quota_check = time.time()
            save_quota_status()
            return f"Error: Permission denied - {e}"

        except (ServiceUnavailable, DeadlineExceeded) as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                return f"Error: Service unavailable after all retries"

        except Exception as e:
            if "quota" in str(e).lower() or "resource_exhausted" in str(e).lower():
                google_quota_exhausted = True
                google_last_quota_check = time.time()
                save_quota_status()
            return f"Error: {str(e)}"

    return "Error: Unknown error"

def translate_deepl(text, target_lang):
    deepl_key = os.getenv('DEEPL_AUTH_KEY', '679719e0-4c2c-4c4e-b0fb-7b9c00d3afa5:fx')
    url = 'https://api-free.deepl.com/v2/translate'
    headers = {
        'Authorization': f'DeepL-Auth-Key {deepl_key}',
        'User-Agent': 'YourApp/1.2.3',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'text': text,
        'target_lang': target_lang
    }
    try:
        response = requests.post(url, headers=headers, data=data, timeout=5)
        if response.status_code == 200:
            return response.json()['translations'][0]['text']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

# =================== Main Loop (scan & translate) =================== #
encText = prev_text = ""
fail_count = 0; max_count = 1000; max_already = 10; already_cnt = 0
while True:
    already_print1 = already_print2 = already_print3 = False
    first_no_char = True; delay_cnt = 0
    # Capture region directly (no red border overlay blocking the loop)
    image1 = ImageGrab.grab(bbox=(x1, y1, x2, y2), include_layered_windows=False, all_screens=True)
    if not image1:
        print("==> 캡처한 영역에 Image가 없습니다!!", end="\r", flush=True)
        time.sleep(0.3)  # delay 0.3초 
        delay_cnt += 1 
        if delay_cnt <= 10:
            continue
    if type(image1) == list:
        print("==> 캡처 준비 중입니다!!", end="\r", flush=True)
        time.sleep(0.1)  # delay 0.1초 
        continue
        
# =================== 화면에서 자막영역의 이미지 캡처 =================== #     
    rgb_image = cv2.cvtColor(np.array(image1), cv2.COLOR_RGB2BGR)
    # 이미지 크기 제한 (최대 한 변 4000)
    max_side = 4000
    h, w = rgb_image.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        rgb_image = cv2.resize(rgb_image, (int(w*scale), int(h*scale)))
    text3 = ocr.predict(rgb_image)

    # PaddleOCR predict() 결과에서 텍스트 추출 (rec_texts 사용)
    text3_j = ""
    if text3 and isinstance(text3, list):
        for block in text3:
            if isinstance(block, dict) and 'rec_texts' in block:
                text3_j += ' '.join(block['rec_texts']) + ' '
    text3_j = text3_j.strip()

    encText = text3_j.replace("  ", " ")
    encText = " ".join(encText.split())
    if not encText: 
        if not already_print1: 
            if first_no_char: 
                first_no_char = False
                continue
            print("==> 캡처한 영역에 글자가 없습니다!!", end="\r", flush=True)
            already_print1 = True
        else:
            print("!", end="\r", flush=True)
        fail_count += 1
        if fail_count > max_count: break
        time.sleep(1)  # delay 1초 
        continue     

    if chars_count(encText) < 5:
        if not already_print2: 
            print("==> 캡처한 영역에 문자가 5자 이하!!", end="\r", flush=True)
            already_print2 = True
        else:
            already_cnt += 1
            if already_cnt > max_already: break
            print("!", end="\r", flush=True)
        fail_count += 1
        if fail_count > max_count: break
        time.sleep(1)  # delay 1초 
        continue
    print()
    prev_len = len(prev_text)
    curr_len = len(encText)    
    max_len = max(prev_len, curr_len)
    max_len = int(max_len * 4/5)
    printed_i = False
    if max_len and prev_text[0:max_len] == encText[0:max_len]:
        if not already_print3: 
            print("==> 캡처한 영역의 내용이 이전과 동일!!", end="\n")
            already_print3 = True
        else:
            print("!", end="\r", flush=True)
            printed_i = True
        fail_count += 1
        if fail_count > max_count: break
        time.sleep(1)  # delay 1초 
        continue

    already_print1 = already_print2 = already_print3 = False
    already_cnt = 0
    prev_text = encText
    if printed_i:
        print('\n',encText)
    else:
        print(encText)
    if sourceLanguage == "chi_sim":        
        chinese_pinyin = pinyin(encText).strip()
        chinese_pinyin = re.sub(r'  ', ' ', chinese_pinyin)
        chinese_pinyin = re.sub(r'^[,。，“\'”"《》? ]+ ', lambda m: re.sub(r' ', '', m.group()), chinese_pinyin)
        chinese_pinyin = re.sub(r' +[,。，“\'”"《》?\- ]+ ', lambda m: re.sub(r' ', '', m.group()), chinese_pinyin)
        chinese_pinyin = re.sub(r'[,。，“\'”"《》? ]+$', lambda m: re.sub(r' ', '', m.group()), chinese_pinyin)
        chinese_pinyin = re.sub(r' +[:;]', lambda m: re.sub(r' ', '', m.group()), chinese_pinyin)
        chinese_pinyin = re.sub(r'  ', ' ', chinese_pinyin)
        print(colored(chinese_pinyin, 'red', 'on_yellow'))
    clipboard.copy(encText)

    windows = pyautogui.getWindowsWithTitle(dictation_file_process)
    for win in windows:
        w = win
    window_activated = False    
    try:
        w.activate()
        window_activated = True    
        time.sleep(0.1)  # Reduced delay for snappier automation
        pyautogui.hotkey('alt', '`')
    except Exception as e:
        print(f"Activation failed: {e}")

# =================== Parallel Translation Execution =================== #
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_baidu = executor.submit(translate_baidu, encText)
        future_google = executor.submit(translate_google, encText)
        future_deepl_ko = executor.submit(translate_deepl, encText, 'Ko')
        future_deepl_en = executor.submit(translate_deepl, encText, 'En')
        future_deepl_de = executor.submit(translate_deepl, encText, 'De')
        
        baidu_res = future_baidu.result()
        google_res = future_google.result()
        deepl_ko_res = future_deepl_ko.result()
        deepl_en_res = future_deepl_en.result()
        deepl_de_res = future_deepl_de.result()

    # Print Baidu Result
    print("Baidu ==> {}".format(baidu_res))

    # Print Google Result
    if not google_res.startswith("Error:"):
        percentage_now = (daily_character_count / daily_character_limit) * 100
        quota_info = f"[{daily_character_count:,}/{daily_character_limit:,} chars, {percentage_now:.1f}%]"
        print(f"Google==> {google_res} {colored(quota_info, 'cyan')}")
        
        # Handle Yuan currency conversion
        if re.search(r"(\d+|[조억만])\s*위안", google_res) and not re.search(r"위안화", google_res):
            try:
                price_KRW = checkYuan_py_v2.checkYuan_RT(google_res)
            except Exception as e:
                print("**Exception: checkYuan_py_v2.checkYuan_RT(trText) ", e)
    else:
        print(f"Google==> {google_res}")
        print(colored("Note: Google Translate unavailable, relying on Baidu and DeepL translations", 'yellow'))

    # Print DeepL Results
    print("DeepL:Ko> {}".format(deepl_ko_res))
    print("DeepL:En> {}".format(deepl_en_res))
    print("DeepL:De> {}".format(deepl_de_res))

# ================================================== # 
    input_str = input("'enter' or border:'bbb' or exit:'xxx' or quota:'qqq' => ")
    if input_str == "xxx":
        break
    elif input_str == "bbb":
        # Show red border overlay around the capture region until ESC is pressed
        show_red_border_until_esc(x1, y1, x2, y2)
    elif input_str == "qqq":
        # Quota management commands
        print("\n=== Google Translate Quota Management ===")
        print(f"Daily usage: {daily_character_count:,} / {daily_character_limit:,} characters")
        percentage_used = (daily_character_count / daily_character_limit) * 100
        print(f"Usage percentage: {percentage_used:.1f}%")
        print(f"Quota exhausted: {'Yes' if google_quota_exhausted else 'No'}")
        print(f"Characters remaining: {daily_character_limit - daily_character_count:,}")
        
        if google_quota_exhausted:
            hours_since_quota = (time.time() - google_last_quota_check) / 3600
            hours_remaining = 24 - hours_since_quota
            print(f"Hours until quota reset: {max(0, hours_remaining):.1f}")
        
        print("\nCommands:")
        print("  'reset' - Force reset quota status (use carefully!)")
        print("  'limit' - Change daily character limit")
        print("  Any other key to continue...")
        
        quota_cmd = input("Enter command: ").lower()
        if quota_cmd == "reset":
            confirm = input("Are you sure you want to reset quota status? (yes/no): ")
            if confirm.lower() == "yes":
                google_quota_exhausted = False
                daily_character_count = 0
                google_last_quota_check = 0
                save_quota_status()
                print(colored("Quota status has been reset!", 'green'))
        elif quota_cmd == "limit":
            try:
                new_limit = int(input(f"Enter new daily limit (current: {daily_character_limit:,}): "))
                if new_limit > 0:
                    daily_character_limit = new_limit
                    print(colored(f"Daily limit updated to {daily_character_limit:,} characters", 'green'))
            except ValueError:
                print(colored("Invalid number entered", 'red'))
        print("Returning to main loop...\n")