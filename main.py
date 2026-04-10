import sys
from PySide6.QtWidgets import QApplication
from core import ConfigManager
from ui import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 關閉所有視窗時不退出程式 (因為我們可能會隱藏主視窗只留彈窗)
    app.setQuitOnLastWindowClosed(False)

    # 1. 載入設定與日誌
    config_manager = ConfigManager()
    config_manager.logger.info("WhAt& App Started.")

    # 2. 啟動主介面
    window = MainWindow(config_manager)
    window.show()

    # 3. 攔截關閉事件來結束應用程式
    app.aboutToQuit.connect(lambda: config_manager.logger.info("WhAt& App Exited."))
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
