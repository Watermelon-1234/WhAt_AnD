import os
import sys
import json
import logging
import platform
from pathlib import Path
from datetime import datetime

class AppContext:
    """處理跨平台路徑，現在預設指向程式執行的根目錄"""
    APP_NAME = "WhatAnd"
    
    @staticmethod
    def get_data_dir() -> Path:
        # 取得 main.py 所在的目錄 (專案根目錄)
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).parent.absolute()
        return base

def play_alert_sound():
    """跨平台的高強度系統提示音"""
    sys_name = platform.system()
    try:
        if sys_name == "Windows":
            import winsound
            # 加上 type: ignore 告訴 Linter 略過此行檢查，解決 Mac/Linux 開發時的報錯
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION) # type: ignore
        elif sys_name == "Darwin": # macOS
            os.system("afplay /System/Library/Sounds/Glass.aiff &")
        else: # Linux
            os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga &")
    except Exception as e:
        print(f"Sound error: {e}")

class LoggerSetup:
    """模組化日誌系統"""
    @staticmethod
    def setup(log_path: Path, level: str = "INFO"):
        logger = logging.getLogger(AppContext.APP_NAME)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        if not logger.handlers:
            fh = logging.FileHandler(log_path / "whatand.log", encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        return logger

class ConfigManager:
    """系統設定管理 (包含 config.json 生成)"""
    def __init__(self):
        self.root_dir = AppContext.get_data_dir()
        self.config_path = self.root_dir / "config.json"
        
        # 預設路徑現在都在專案根目錄下
        self.default_session_dir = str(self.root_dir / "Sessions")
        self.default_log_dir = str(self.root_dir / "Logs")
        
        self.config = {
            "theme": "dark",
            "language": "en",
            "volume": 50,
            "autostart": False,
            "log_path": self.default_log_dir,
            "log_level": "INFO",
            "session_dir": self.default_session_dir
        }
        self.load()
        
        # 確保資料夾存在
        Path(self.config["session_dir"]).mkdir(parents=True, exist_ok=True)
        Path(self.config["log_path"]).mkdir(parents=True, exist_ok=True)
        
        self.logger = LoggerSetup.setup(Path(self.config["log_path"]), self.config["log_level"])
        self.save() # 確保首次執行一定會產出 config.json

    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def reset_to_default(self):
        self.config["theme"] = "dark"
        self.config["session_dir"] = self.default_session_dir
        self.config["log_path"] = self.default_log_dir
        self.save()

class SessionManager:
    """管理專注 Session 的資料與 JSON 寫入"""
    def __init__(self, session_dir: str):
        self.session_dir = Path(session_dir)
        self.session_name = ""
        self.time_interval = 0
        self.history = []
        self.file_path = None

    def start_new(self, name: str, interval: int):
        self.session_name = name
        self.time_interval = interval
        self.history = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = self.session_dir / f"{self.session_name}_{timestamp}.json"
        self.save()

    def add_record(self, content: str):
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": content
        }
        self.history.append(record)
        self.save()

    def save(self):
        if not self.file_path: return
        data = {
            "session_name": self.session_name,
            "time_interval": self.time_interval,
            "history": self.history
        }
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)