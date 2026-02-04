from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QComboBox, 
                             QProgressBar, QGroupBox, QCheckBox) # Added QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal

class ExportDialog(QDialog):
    # Updated Signal: Now includes 'split_screen' (bool)
    export_requested = pyqtSignal(str, str, int, bool) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Video")
        self.resize(500, 450) # Made slightly taller
        self.layout = QVBoxLayout(self)

        # 1. Music Selection
        grp_audio = QGroupBox("Audio Sync")
        audio_layout = QVBoxLayout()
        
        self.lbl_audio = QLabel("No Audio Selected (Silent Video)")
        self.btn_select_audio = QPushButton("Select MP3/WAV")
        self.btn_select_audio.clicked.connect(self.select_audio)
        
        audio_layout.addWidget(self.lbl_audio)
        audio_layout.addWidget(self.btn_select_audio)
        grp_audio.setLayout(audio_layout)
        self.layout.addWidget(grp_audio)

        # 2. Video Settings
        grp_video = QGroupBox("Video Settings")
        video_layout = QVBoxLayout() # Changed to VBox for cleaner stacking
        
        # Row 1: Presets
        row_settings = QHBoxLayout()
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(["TikTok/Reels (1080x1920)", "YouTube (Landscape)", "Square (Instagram)"])
        
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["30 FPS", "60 FPS", "24 FPS"])
        
        row_settings.addWidget(QLabel("Preset:"))
        row_settings.addWidget(self.combo_preset)
        row_settings.addWidget(QLabel("Frame Rate:"))
        row_settings.addWidget(self.combo_fps)
        
        # Row 2: Split Screen (NEW)
        self.chk_split = QCheckBox("Split-Screen Comparison (Start vs. Now)")
        self.chk_split.setToolTip("Creates a side-by-side video: Day 1 Static (Left) vs Timelapse (Right)")

        video_layout.addLayout(row_settings)
        video_layout.addWidget(self.chk_split)
        
        grp_video.setLayout(video_layout)
        self.layout.addWidget(grp_video)

        # 3. Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("Render Video")
        self.btn_export.setStyleSheet("background-color: #00E676; color: black; font-weight: bold; padding: 10px;")
        self.btn_export.clicked.connect(self.on_export_click)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_export)
        self.layout.addLayout(btn_layout)

        self.selected_audio_path = None

    def select_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Music", "", "Audio Files (*.mp3 *.wav *.m4a)")
        if path:
            self.selected_audio_path = path
            self.lbl_audio.setText(f"Selected: {path.split('/')[-1]}")

    def on_export_click(self):
        fps = int(self.combo_fps.currentText().split(" ")[0])
        preset = self.combo_preset.currentText()
        is_split = self.chk_split.isChecked() # Get Checkbox state
        
        # Lock UI
        self.btn_export.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_label.setText("Analyzing Audio...")
        
        # Emit Signal
        self.export_requested.emit(self.selected_audio_path, preset, fps, is_split)

    def update_progress(self, val):
        self.progress.setValue(val)
        if val < 50:
            self.status_label.setText("Assembling Frames...")
        elif val < 90:
            self.status_label.setText("Encoding Video (This takes CPU power)...")
        else:
            self.status_label.setText("Finalizing...")

    def export_finished(self):
        self.status_label.setText("Done!")
        self.btn_export.setEnabled(True)
        self.btn_export.setText("Export Again")