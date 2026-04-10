import json
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QLineEdit, QSlider, QDialog, QApplication, 
                               QComboBox, QListWidget, QSizePolicy, QStackedWidget,
                               QFileDialog)
from PySide6.QtGui import QFont, QGuiApplication, QCursor
from PySide6.QtCore import Qt, QTimer
from core import ConfigManager, SessionManager, play_alert_sound
import platform

# UI 樣式設定
STYLESHEET_DARK = """
QWidget { background-color: #222222; color: #F5F2E9; font-family: 'Segoe UI', Arial, sans-serif; font-size: 16px;}
QPushButton { background-color: #333333; color: #F5F2E9; font-weight: bold; border: 2px solid #555555; border-radius: 8px; font-size: 16px;}
QPushButton:hover { background-color: #444444; border-color: #777777; }
QPushButton:pressed { background-color: #555555; }
QLineEdit { background-color: #111111; border: 2px solid #555555; padding: 10px; color: #F5F2E9; font-weight: bold; border-radius: 8px; font-size: 18px;}
QLineEdit:focus { border: 2px solid #888888; }
QSlider::groove:horizontal { border: 1px solid #444444; height: 10px; background: #111111; margin: 2px 0; border-radius: 5px;}
QSlider::handle:horizontal { background: #F5F2E9; border: 1px solid #aaaaaa; width: 18px; margin: -5px 0; border-radius: 9px; }

/* 新增 Focus 視窗的邊框設定 */
#FocusDisplay {
    border: 3px solid #777777;
    border-radius: 12px;
}
"""

STYLESHEET_LIGHT = """
QWidget { background-color: #E8E5DC; color: #222222; font-family: 'Segoe UI', Arial, sans-serif; font-size: 16px;}
QPushButton { background-color: #DCD8CC; color: #222222; font-weight: bold; border: 2px solid #B0ADA3; border-radius: 8px; font-size: 16px;}
QPushButton:hover { background-color: #D0CCC0; border-color: #888888; }
QLineEdit { background-color: #F5F2E9; border: 2px solid #B0ADA3; padding: 10px; color: #222222; font-weight: bold; border-radius: 8px; font-size: 18px;}
QLineEdit:focus { border: 2px solid #666666; }

/* 新增 Focus 視窗的邊框設定 */
#FocusDisplay {
    border: 3px solid #888888;
    border-radius: 12px;
}
"""

class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.cm = config_manager
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.cm.config["theme"])
        self.theme_combo.setFixedHeight(40)
        layout.addWidget(QLabel("Theme:"))
        layout.addWidget(self.theme_combo)

        # Session 目錄設定
        layout.addWidget(QLabel("Session Directory:"))
        sess_layout = QHBoxLayout()
        self.sess_input = QLineEdit(self.cm.config["session_dir"])
        self.sess_input.setFixedHeight(40)
        sess_btn = QPushButton("Browse")
        sess_btn.setFixedHeight(40)
        sess_btn.clicked.connect(lambda: self.browse_dir(self.sess_input))
        sess_layout.addWidget(self.sess_input)
        sess_layout.addWidget(sess_btn)
        layout.addLayout(sess_layout)

        # Log 目錄設定
        layout.addWidget(QLabel("Log Directory:"))
        log_layout = QHBoxLayout()
        self.log_input = QLineEdit(self.cm.config["log_path"])
        self.log_input.setFixedHeight(40)
        log_btn = QPushButton("Browse")
        log_btn.setFixedHeight(40)
        log_btn.clicked.connect(lambda: self.browse_dir(self.log_input))
        log_layout.addWidget(self.log_input)
        log_layout.addWidget(log_btn)
        layout.addLayout(log_layout)

        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset Default")
        reset_btn.setFixedHeight(45)
        reset_btn.clicked.connect(self.reset_defaults)
        save_btn = QPushButton("Save")
        save_btn.setFixedHeight(45)
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(save_btn)
        layout.addSpacing(15)
        layout.addLayout(btn_layout)

    def browse_dir(self, line_edit):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if dir_path:
            line_edit.setText(dir_path)

    def reset_defaults(self):
        self.cm.reset_to_default()
        self.accept()

    def save_settings(self):
        self.cm.config["theme"] = self.theme_combo.currentText()
        self.cm.config["session_dir"] = self.sess_input.text()
        self.cm.config["log_path"] = self.log_input.text()
        self.cm.save()
        self.accept()

class NewSessionDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False, current_interval=0, current_name=""):
        super().__init__(parent)
        self.setWindowTitle("Edit Session" if edit_mode else "New Session")
        self.setMinimumWidth(400)
        self.interval_seconds = current_interval
        self.session_name = current_name
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Session Name:"))
        self.name_input = QLineEdit(self.session_name)
        self.name_input.setFixedHeight(45)
        self.name_input.setReadOnly(edit_mode)
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Interval Magnitude (Sec / Min / Hr):"))
        self.mag_slider = QSlider(Qt.Orientation.Horizontal)
        self.mag_slider.setRange(0, 2)
        self.mag_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        layout.addWidget(self.mag_slider)

        layout.addWidget(QLabel("Interval Fine-tune (1-60):"))
        self.val_slider = QSlider(Qt.Orientation.Horizontal)
        self.val_slider.setRange(1, 60)
        layout.addWidget(self.val_slider)

        self.preview_label = QLabel("Calculated Interval: 0 seconds")
        layout.addWidget(self.preview_label)

        self.mag_slider.valueChanged.connect(self.update_preview)
        self.val_slider.valueChanged.connect(self.update_preview)

        if current_interval > 0:
            if current_interval >= 3600:
                self.mag_slider.setValue(2)
                self.val_slider.setValue(max(1, current_interval // 3600))
            elif current_interval >= 60:
                self.mag_slider.setValue(1)
                self.val_slider.setValue(max(1, current_interval // 60))
            else:
                self.mag_slider.setValue(0)
                self.val_slider.setValue(current_interval)
        else:
            self.mag_slider.setValue(1)
            self.val_slider.setValue(15)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(45)
        cancel_btn.clicked.connect(self.reject)
        start_btn = QPushButton("Start" if not edit_mode else "Update")
        start_btn.setFixedHeight(45)
        start_btn.clicked.connect(self.accept_data)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(start_btn)
        layout.addLayout(btn_layout)
        self.update_preview()

    def update_preview(self):
        mag = self.mag_slider.value()
        val = self.val_slider.value()
        multiplier = 1 if mag == 0 else (60 if mag == 1 else 3600)
        self.interval_seconds = val * multiplier
        unit = "Seconds" if mag == 0 else ("Minutes" if mag == 1 else "Hours")
        self.preview_label.setText(f"Calculated Interval: {val} {unit} ({self.interval_seconds}s)")

    def accept_data(self):
        self.session_name = self.name_input.text() or "Unnamed_Session"
        self.accept()

class OldSessionDialog(QDialog):
    def __init__(self, session_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Old Sessions")
        self.setMinimumWidth(400)
        self.session_dir = Path(session_dir)
        self.selected_file = None
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for file in self.session_dir.glob("*.json"):
            self.list_widget.addItem(file.name)
        layout.addWidget(self.list_widget)

        start_btn = QPushButton("Start Selected")
        start_btn.setFixedHeight(45)
        start_btn.clicked.connect(self.start_session)
        layout.addWidget(start_btn)

    def start_session(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_file = self.session_dir / item.text()
            self.accept()

class PopupWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.last_answer = ""
        self.set_topmost_flags()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用堆疊佈局切換「輸入模式」與「常駐顯示模式」
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # ===== 模式1：輸入介面 =====
        self.input_widget = QWidget()
        input_layout = QVBoxLayout(self.input_widget)
        input_layout.setContentsMargins(20, 20, 20, 20)
        
        top_layout = QHBoxLayout()
        self.title_label = QLabel("WhAt& - What are you doing right now?")
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setFixedSize(45, 45)
        self.edit_btn.clicked.connect(self.edit_session)
        
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(45, 45)
        self.close_btn.clicked.connect(self.skip_input)
        
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.edit_btn)
        top_layout.addWidget(self.close_btn)
        input_layout.addLayout(top_layout)

        # 輸入框
        self.input_field = QLineEdit()
        self.input_field.setFixedHeight(60) 
        self.input_field.setPlaceholderText("Enter your current task...")
        self.input_field.returnPressed.connect(self.submit)
        input_layout.addWidget(self.input_field)

        bot_layout = QHBoxLayout()
        self.same_btn = QPushButton("Same as last time")
        self.same_btn.setFixedHeight(50)
        self.same_btn.clicked.connect(self.submit_same)
        self.same_btn.setEnabled(False)
        
        stop_btn = QPushButton("Stop Session")
        stop_btn.setFixedHeight(50)
        stop_btn.clicked.connect(self.stop_session)
        
        submit_btn = QPushButton("Submit")
        submit_btn.setFixedHeight(50)
        submit_btn.clicked.connect(self.submit)
        
        bot_layout.addWidget(self.same_btn)
        bot_layout.addWidget(stop_btn)
        bot_layout.addWidget(submit_btn)
        input_layout.addLayout(bot_layout)

        # ===== 模式2：常駐顯示介面 =====
        self.display_widget = QWidget()
        self.display_widget.setObjectName("FocusDisplay") # 給予 ID 讓樣式表套用邊框
        
        # 改成水準排列 (QHBoxLayout) 以便把標籤和按鈕排在同一行
        display_layout = QHBoxLayout(self.display_widget)
        display_layout.setContentsMargins(15, 10, 15, 10)
        
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        display_layout.addWidget(self.display_label)

        # 增加退出 (Stop) 按鈕
        self.display_stop_btn = QPushButton("Stop")
        self.display_stop_btn.setFixedSize(60, 40)
        self.display_stop_btn.clicked.connect(self.stop_session)
        display_layout.addWidget(self.display_stop_btn)

        # 將兩種介面加入堆疊
        self.stack.addWidget(self.input_widget)
        self.stack.addWidget(self.display_widget)

    def set_topmost_flags(self):
        """暴力強制置頂：恢復 WindowStaysOnTopHint 與跨桌面屬性"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnTopHint 
        )
        
        # 針對 macOS：嘗試強制 Tool 視窗在所有桌面 (Spaces) 及全螢幕應用程式之上顯示
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)

    def showEvent(self, event):
        """當視窗顯示時，觸發 macOS 的跨桌面屬性設定"""
        super().showEvent(event)
        self.set_mac_spaces_behavior()

    def set_mac_spaces_behavior(self):
        """macOS 專用：強制視窗穿透所有虛擬桌面 (Spaces)"""
        if platform.system() == "Darwin":
            try:
                import objc
                # 這次我們多引入了 MoveToActiveSpace 這個常數來拔除它
                from AppKit import ( # type: ignore
                    NSWindowCollectionBehaviorCanJoinAllSpaces, 
                    NSWindowCollectionBehaviorMoveToActiveSpace
                )
                
                # PySide6 的 winId() 在 macOS 會回傳 NSView 的記憶體指標
                view_ptr = int(self.winId())
                
                ns_view = objc.objc_object(c_void_p=view_ptr) # type: ignore
                ns_window = ns_view.window()
                
                if ns_window:
                    # 取得當前屬性
                    behavior = ns_window.collectionBehavior()
                    
                    # 核心修正：先「抹除」Qt 自動加上的 MoveToActiveSpace 衝突屬性 (使用 bitwise NOT AND)
                    behavior &= ~NSWindowCollectionBehaviorMoveToActiveSpace
                    
                    # 然後再「加上」我們想要的 CanJoinAllSpaces 屬性 (使用 bitwise OR)
                    behavior |= NSWindowCollectionBehaviorCanJoinAllSpaces
                    
                    # 寫回設定
                    ns_window.setCollectionBehavior_(behavior)
                    
            except ImportError:
                print("請在終端機執行: pip install pyobjc 來啟用跨桌面功能")
            except Exception as e:
                print(f"macOS 跨桌面設定失敗: {e}")

    # --- 支援無邊框視窗拖曳 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def switch_to_input(self):
        self.stack.setCurrentIndex(0)
        self.setFixedSize(650, 280) 
        self.input_field.clear()
        self.input_field.setFocus()
        
        screen = QGuiApplication.screenAt(QCursor.pos())
        if not screen: # 如果抓不到，退而求其次抓主螢幕
            screen = QGuiApplication.primaryScreen()
            
        if screen:
            geom = screen.geometry()
            self.move(geom.x() + (geom.width() - self.width()) // 2, geom.y() + (geom.height() - self.height()) // 2)

    def switch_to_display(self):
        self.display_label.setText(f"Focus: {self.last_answer}")
        self.stack.setCurrentIndex(1)
        # 把寬度從 300 加大到 380，高度也可以微調成 75，容納新按鈕與邊框
        self.setFixedSize(380, 75) 
        self.main_window.reset_timer() # 開始倒數下次彈窗

    def submit(self):
        text = self.input_field.text().strip()
        if text:
            self.last_answer = text
            self.same_btn.setEnabled(True)
            self.main_window.record_answer(text)
            self.switch_to_display()

    def submit_same(self):
        if self.last_answer:
            self.main_window.record_answer(self.last_answer)
            self.switch_to_display()

    def skip_input(self):
        if self.last_answer:
            self.switch_to_display() # 略過則退回前一個常駐目標
        else:
            self.hide()
            self.main_window.reset_timer()

    def edit_session(self):
        dialog = NewSessionDialog(self, edit_mode=True, 
                                  current_interval=self.main_window.session.time_interval,
                                  current_name=self.main_window.session.session_name)
        if dialog.exec():
            self.main_window.session.time_interval = dialog.interval_seconds
            self.main_window.session.save()
            self.skip_input()

    def stop_session(self):
        self.hide()
        self.main_window.stop_session()

class MainWindow(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.cm = config_manager
        self.session = SessionManager(self.cm.config["session_dir"])
        self.popup = PopupWindow(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_popup)
        
        # 核心改動：根據 SO 解法監聽全域焦點改變事件
        # 透過 isinstance 確保 Pylance 知道這是一個具有 focusChanged 屬性的 QApplication，且不是 None
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.focusChanged.connect(self.on_focus_changed)
        
        self.init_ui()
        self.apply_theme()

    def on_focus_changed(self, old, new):
        """
        當應用程式內的焦點改變時，若焦點來到 MainWindow (或其子元件)，
        就把 popup 提升到最上層，避免 popup 被主視窗遮擋。
        """
        if new is not None and new.window() == self:
            if self.popup.isVisible():
                self.popup.raise_()

    def init_ui(self):
        self.setWindowTitle("WhAt&")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        btn_size = 140 # 主畫面按鈕大小

        new_btn = QPushButton("New\nSession")
        new_btn.setFixedSize(btn_size, btn_size)
        new_btn.clicked.connect(self.start_new_session)
        layout.addWidget(new_btn)

        old_btn = QPushButton("Old\nSession")
        old_btn.setFixedSize(btn_size, btn_size)
        old_btn.clicked.connect(self.start_old_session)
        layout.addWidget(old_btn)

        set_btn = QPushButton("Settings")
        set_btn.setFixedSize(btn_size, btn_size)
        set_btn.clicked.connect(self.open_settings)
        layout.addWidget(set_btn)

        # 退出按鈕
        exit_btn = QPushButton("Exit\nApp")
        exit_btn.setFixedSize(btn_size, btn_size)
        exit_btn.clicked.connect(self.quit_app)  # 順便修正了之前的 Pylance None 警告
        layout.addWidget(exit_btn)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.adjustSize() 
        self.setFixedSize(self.sizeHint())

    def quit_app(self):
        app = QApplication.instance()
        if app:
            app.quit()

    def apply_theme(self):
        theme = self.cm.config.get("theme", "dark")
        if theme == "dark":
            self.setStyleSheet(STYLESHEET_DARK)
            self.popup.setStyleSheet(STYLESHEET_DARK)
        else:
            self.setStyleSheet(STYLESHEET_LIGHT)
            self.popup.setStyleSheet(STYLESHEET_LIGHT)

    def start_new_session(self):
        dialog = NewSessionDialog(self)
        if dialog.exec():
            self.session = SessionManager(self.cm.config["session_dir"]) 
            self.session.start_new(dialog.session_name, dialog.interval_seconds)
            self.cm.logger.info(f"Started new session: {dialog.session_name} ({dialog.interval_seconds}s)")
            self.begin_timer()

    def start_old_session(self):
        dialog = OldSessionDialog(self.cm.config["session_dir"], self)
        if dialog.exec() and dialog.selected_file:
            with open(dialog.selected_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.session = SessionManager(self.cm.config["session_dir"])
            self.session.file_path = dialog.selected_file
            self.session.session_name = data.get("session_name", "Loaded_Session")
            self.session.time_interval = data.get("time_interval", 900)
            self.session.history = data.get("history", [])
            self.cm.logger.info(f"Resumed session: {self.session.session_name}")
            self.begin_timer()

    def open_settings(self):
        dialog = SettingsDialog(self.cm, self)
        if dialog.exec():
            self.apply_theme()

    def begin_timer(self):
        self.hide()
        self.show_popup() # 開始時直接觸發第一次詢問

    def reset_timer(self):
        self.timer.stop()
        self.timer.start(self.session.time_interval * 1000)

    def show_popup(self):
        self.timer.stop()
        
        # 強制隱藏，打破作業系統的視窗緩存限制
        self.popup.hide() 
        
        self.popup.set_topmost_flags()
        self.popup.switch_to_input()
        
        self.popup.show()
        self.popup.raise_()       
        self.popup.activateWindow() 
        
        # 強制取消最小化狀態 (保險機制)
        self.popup.setWindowState(self.popup.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        
        play_alert_sound() 

    def record_answer(self, text):
        self.session.add_record(text)
        self.cm.logger.info(f"Recorded: {text}")

    def stop_session(self):
        self.timer.stop()
        self.session.save()
        self.popup.last_answer = ""
        self.cm.logger.info(f"Session stopped: {self.session.session_name}")
        self.show()