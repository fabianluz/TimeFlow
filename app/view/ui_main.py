from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QProgressBar, 
                             QScrollArea, QGridLayout, QFrame, QStackedWidget, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent, QFont
from app.view.heatmap_widget import HeatmapWidget
from app.view.editor_view import EditorView

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit()
        super().mousePressEvent(event)

class TimeFlowWindow(QMainWindow):
    files_dropped = pyqtSignal(list)
    photo_selected = pyqtSignal(str) 

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimeFlow")
        self.resize(1100, 850)
        self.setAcceptDrops(True)
        
        # Set a cleaner base style for the whole window
        self.setStyleSheet("""
            QMainWindow { background-color: #F5F5F7; }
            QWidget { font-family: 'SF Pro Display', 'Helvetica Neue', sans-serif; }
        """)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.page_dashboard = QWidget()
        self.setup_dashboard()
        self.stack.addWidget(self.page_dashboard)

        self.editor = EditorView()
        self.stack.addWidget(self.editor)

    def setup_dashboard(self):
        main_layout = QVBoxLayout(self.page_dashboard)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        # --- HEADER SECTION ---
        header = QHBoxLayout()
        
        title_container = QVBoxLayout()
        self.lbl_title = QLabel("Your Timeline")
        self.lbl_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1D1D1F;")
        self.lbl_subtitle = QLabel("Sync your progress and create your story.")
        self.lbl_subtitle.setStyleSheet("font-size: 14px; color: #86868B;")
        title_container.addWidget(self.lbl_title)
        title_container.addWidget(self.lbl_subtitle)
        
        header.addLayout(title_container)
        header.addStretch()
        
        # Dashboard Action Buttons
        self.btn_export = QPushButton("Create Video")
        self.btn_export.setFixedSize(140, 40)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #0071E3; color: white; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #0077ED; }
        """)
        
        self.btn_ingest = QPushButton("+ Add Photo")
        self.btn_ingest.setFixedSize(120, 40)
        self.btn_ingest.setStyleSheet("""
            QPushButton {
                background-color: #E8E8ED; color: #1D1D1F; border-radius: 8px; font-weight: 500;
            }
            QPushButton:hover { background-color: #D2D2D7; }
        """)
        
        header.addWidget(self.btn_ingest)
        header.addWidget(self.btn_export)
        main_layout.addLayout(header)

        # Heatmap Container (Card Style)
        heatmap_container = QFrame()
        heatmap_container.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #D2D2D7;")
        heatmap_layout = QVBoxLayout(heatmap_container)
        self.heatmap = HeatmapWidget()
        heatmap_layout.addWidget(self.heatmap)
        main_layout.addWidget(heatmap_container)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background-color: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(25)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        # Progress / Status Bar
        footer = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #86868B; font-size: 12px;")
        self.progress = QProgressBar()
        self.progress.setFixedSize(200, 6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar { background-color: #E8E8ED; border-radius: 3px; }
            QProgressBar::chunk { background-color: #0071E3; border-radius: 3px; }
        """)
        self.progress.setVisible(False)
        
        footer.addWidget(self.status_label)
        footer.addStretch()
        footer.addWidget(self.progress)
        main_layout.addLayout(footer)

    def add_photo_to_grid(self, pixmap, date_text, row, col, file_id):
        card = QFrame()
        card.setFixedSize(220, 260)
        card.setStyleSheet("""
            QFrame {
                background-color: white; border-radius: 15px; 
                border: 1px solid #D2D2D7;
            }
            QFrame:hover { border: 2px solid #0071E3; }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        
        img_label = ClickableLabel()
        img_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet("border: none; border-radius: 10px;")
        img_label.clicked.connect(lambda: self.photo_selected.emit(file_id))
        
        date_label = QLabel(date_text)
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setStyleSheet("font-size: 11px; color: #1D1D1F; font-weight: 500; border: none; margin-top: 5px;")
        
        card_layout.addWidget(img_label)
        card_layout.addWidget(date_label)
        self.grid_layout.addWidget(card, row, col)

    # Drag and Drop events (unchanged logic)
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            self.files_dropped.emit(files)
            event.acceptProposedAction()