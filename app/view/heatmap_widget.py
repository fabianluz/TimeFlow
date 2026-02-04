from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QSize
from datetime import datetime, timedelta

class HeatmapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(80)
        self.active_dates = set()

    def set_data(self, db_photos):
        self.active_dates.clear()
        for timestamp in db_photos.keys():
            self.active_dates.add(timestamp[:10])
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        box_size = 18
        spacing = 6
        start_x = 20
        y_pos = 30

        
        color_empty = QColor("
        color_filled = QColor("

        today = datetime.now()
        
        for i in range(29, -1, -1):
            target_date = today - timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")

            painter.setBrush(QBrush(color_filled if date_str in self.active_dates else color_empty))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(start_x, y_pos, box_size, box_size, 5, 5)

            
            if i == 29 or i == 0:
                painter.setPen(QColor("
                font = painter.font()
                font.setPointSize(9)
                painter.setFont(font)
                painter.drawText(start_x, y_pos - 8, target_date.strftime("%b %d"))

            start_x += (box_size + spacing)
            
    def sizeHint(self):
        return QSize(800, 80)