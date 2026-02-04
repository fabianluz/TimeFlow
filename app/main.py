import sys
from PyQt6.QtWidgets import QApplication
from app.view.ui_main import TimeFlowWindow
from app.controller.app_controller import AppController

def main():
    app = QApplication(sys.argv)
    
    
    
    

    window = TimeFlowWindow()
    controller = AppController(window)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()