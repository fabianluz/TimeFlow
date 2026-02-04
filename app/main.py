import sys
from PyQt6.QtWidgets import QApplication
from app.view.ui_main import TimeFlowWindow
from app.controller.app_controller import AppController

def main():
    app = QApplication(sys.argv)
    
    # We remove qt-material and let our custom stylesheets do the work
    # Or use a very light material theme if you prefer:
    # apply_stylesheet(app, theme='light_blue.xml')

    window = TimeFlowWindow()
    controller = AppController(window)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()