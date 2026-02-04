from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSlider, QGraphicsView, 
                             QGraphicsScene, QGraphicsPixmapItem, QCheckBox, 
                             QGraphicsPathItem, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPen, QColor, QPainterPath

class EditorView(QWidget):
    
    back_clicked = pyqtSignal()
    rotate_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    undo_clicked = pyqtSignal()
    
    
    auto_align_clicked = pyqtSignal()
    deflicker_clicked = pyqtSignal()
    gap_fill_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.setStyleSheet("background-color: 
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        
        self.view.setStyleSheet("""
            QGraphicsView {
                background: 
                border: 1px solid 
                border-radius: 20px;
            }
        """)
        self.layout.addWidget(self.view)

        
        self.controls_panel = QFrame()
        self.controls_panel.setFixedHeight(140)
        self.controls_panel.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 18px; 
                border: 1px solid 
            }
        """)
        panel_layout = QVBoxLayout(self.controls_panel)
        panel_layout.setContentsMargins(20, 10, 20, 15)

        
        row_visuals = QHBoxLayout()
        
        lbl_opacity = QLabel("Layer Opacity")
        lbl_opacity.setStyleSheet("font-size: 13px; font-weight: 600; color: 
        
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(70)
        self.slider_opacity.setFixedWidth(250)
        self.slider_opacity.setStyleSheet("""
            QSlider::groove:horizontal { background: 
            QSlider::handle:horizontal { background: 
        """)
        self.slider_opacity.valueChanged.connect(self.update_opacity)

        self.chk_skeleton = QCheckBox("Body Guide Overlay")
        self.chk_skeleton.setStyleSheet("font-size: 13px; color: 
        self.chk_skeleton.stateChanged.connect(self.toggle_skeleton)
        
        row_visuals.addWidget(lbl_opacity)
        row_visuals.addWidget(self.slider_opacity)
        row_visuals.addSpacing(30)
        row_visuals.addWidget(self.chk_skeleton)
        row_visuals.addStretch()
        panel_layout.addLayout(row_visuals)

        
        row_buttons = QHBoxLayout()
        
        
        self.btn_auto_align = QPushButton("Auto-Align")
        self.btn_deflicker = QPushButton("Deflicker")
        self.btn_gap_fill = QPushButton("Fill Gap")
        self.btn_rotate = QPushButton("Rotate")
        self.btn_undo = QPushButton("Undo")
        
        
        self.btn_save = QPushButton("Apply & Close")
        self.btn_cancel = QPushButton("Cancel")

        
        primary_style = """
            QPushButton { background-color: 
            QPushButton:hover { background-color: 
        """
        secondary_style = """
            QPushButton { background-color: 
            QPushButton:hover { background-color: 
        """
        destructive_style = """
            QPushButton { background-color: transparent; color: 
            QPushButton:hover { text-decoration: underline; }
        """

        self.btn_auto_align.setStyleSheet(secondary_style)
        self.btn_deflicker.setStyleSheet(secondary_style)
        self.btn_gap_fill.setStyleSheet(secondary_style)
        self.btn_rotate.setStyleSheet(secondary_style)
        self.btn_undo.setStyleSheet(secondary_style)
        self.btn_save.setStyleSheet(primary_style)
        self.btn_cancel.setStyleSheet(destructive_style)

        
        self.btn_auto_align.clicked.connect(self.auto_align_clicked.emit)
        self.btn_deflicker.clicked.connect(self.deflicker_clicked.emit)
        self.btn_gap_fill.clicked.connect(self.gap_fill_clicked.emit)
        self.btn_rotate.clicked.connect(self.rotate_clicked.emit)
        self.btn_undo.clicked.connect(self.undo_clicked.emit)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_cancel.clicked.connect(self.back_clicked.emit)

        
        row_buttons.addWidget(self.btn_auto_align)
        row_buttons.addWidget(self.btn_deflicker)
        row_buttons.addWidget(self.btn_gap_fill)
        row_buttons.addSpacing(15)
        row_buttons.addWidget(self.btn_rotate)
        row_buttons.addWidget(self.btn_undo)
        row_buttons.addStretch()
        row_buttons.addWidget(self.btn_cancel)
        row_buttons.addWidget(self.btn_save)
        panel_layout.addLayout(row_buttons)

        self.layout.addWidget(self.controls_panel)

    
    def load_images(self, active_path, ghost_path=None):
        self.scene.clear()
        if ghost_path:
            pix_ghost = QPixmap(ghost_path)
            self.ghost_item = self.scene.addPixmap(pix_ghost)
            self.ghost_item.setOpacity(1.0) 
        pix_active = QPixmap(active_path)
        self.active_item = self.scene.addPixmap(pix_active)
        self.active_item.setZValue(1) 
        self.view.setSceneRect(self.active_item.boundingRect())
        self.update_opacity(self.slider_opacity.value())
        self.scene.update()

    def update_opacity(self, value):
        if hasattr(self, 'active_item') and self.active_item:
            self.active_item.setOpacity(value / 100.0)

    def refresh_active(self, path):
        if hasattr(self, 'active_item') and self.active_item:
            self.active_item.setPixmap(QPixmap(path))

    def draw_skeleton(self, landmarks, width, height):
        if hasattr(self, 'skeleton_item') and self.skeleton_item:
            self.scene.removeItem(self.skeleton_item)
        if not landmarks: return
        connections = [(11, 12), (11, 23), (12, 24), (23, 24), (11, 13), (13, 15), (12, 14), (14, 16), (0, 11), (0, 12)]
        path = QPainterPath()
        for start, end in connections:
            if start < len(landmarks) and end < len(landmarks):
                path.moveTo(landmarks[start][0] * width, landmarks[start][1] * height)
                path.lineTo(landmarks[end][0] * width, landmarks[end][1] * height)
        self.skeleton_item = QGraphicsPathItem(path)
        self.skeleton_item.setPen(QPen(QColor("
        self.skeleton_item.setZValue(2)
        self.scene.addItem(self.skeleton_item)

    def toggle_skeleton(self):
        if hasattr(self, 'skeleton_item') and self.skeleton_item:
            self.skeleton_item.setVisible(self.chk_skeleton.isChecked())