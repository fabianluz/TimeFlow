import os
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap
from PIL import Image 

from app.model.file_manager import FileManager
from app.model.ai_pose import PoseDetector
from app.model.audio_processor import AudioProcessor
from app.model.video_renderer import VideoRenderer
from app.view.export_dialog import ExportDialog

from app.controller.commands import (
    CommandInvoker, 
    RotateCommand, 
    AutoAlignCommand, 
    DeflickerCommand,
    GenerateGapFillCommand
)


class IngestWorker(QObject):
    finished = pyqtSignal(str, str) 
    def __init__(self, file_manager, file_path):
        super().__init__()
        self.manager = file_manager
        self.path = file_path
    def run(self):
        file_id, date_str = self.manager.ingest_photo(self.path)
        self.finished.emit(file_id, date_str)


class RenderWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(self, output_path, photos, audio_path, fps, split_screen):
        super().__init__()
        self.output_path = output_path
        self.photos = photos
        self.audio_path = audio_path
        self.fps = fps
        self.split_screen = split_screen 

    def run(self):
        
        schedule = None
        if self.audio_path:
            processor = AudioProcessor()
            processor.load_audio(self.audio_path)
            schedule = processor.get_sync_schedule(len(self.photos))

        
        renderer = VideoRenderer(
            self.output_path, 
            self.photos, 
            self.audio_path, 
            schedule, 
            self.fps,
            self.split_screen 
        )
        success = renderer.render(self.update_progress)
        self.finished.emit(success)

    def update_progress(self, val):
        self.progress.emit(val)



class AppController:
    def __init__(self, view):
        self.view = view
        
        
        desktop = os.path.join(os.path.expanduser("~"), "Desktop", "TimeFlow_Project")
        self.model = FileManager(desktop)
        self.invoker = CommandInvoker()
        self.ai_pose = PoseDetector()
        
        self.current_editing_id = None
        self.sorted_ids = []

        
        self.view.btn_ingest.clicked.connect(self.select_file)
        self.view.files_dropped.connect(self.handle_drop)
        self.view.photo_selected.connect(self.enter_editor)
        self.view.btn_export.clicked.connect(self.open_export_dialog)

        
        self.view.editor.back_clicked.connect(self.exit_editor)
        self.view.editor.rotate_clicked.connect(self.rotate_image)
        self.view.editor.undo_clicked.connect(self.undo_action)
        self.view.editor.save_clicked.connect(self.exit_editor)
        
        self.view.editor.auto_align_clicked.connect(self.run_auto_align)
        self.view.editor.deflicker_clicked.connect(self.run_deflicker)
        self.view.editor.gap_fill_clicked.connect(self.run_gap_fill)

        
        self.refresh_grid()

    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Select Photo", "", "Images (*.png *.jpg *.jpeg *.heic)")
        if file_path:
            self.start_ingest(file_path)

    def handle_drop(self, file_paths):
        valid = ('.jpg', '.jpeg', '.png', '.heic')
        for f in file_paths:
            if f.lower().endswith(valid):
                self.start_ingest(f)
                return 

    def start_ingest(self, file_path):
        self.view.status_label.setText(f"Processing {os.path.basename(file_path)}...")
        self.view.progress.setVisible(True)
        self.view.progress.setRange(0, 0)
        
        self.thread = QThread()
        self.worker = IngestWorker(self.model, file_path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_ingest_done)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_ingest_done(self, file_id, date_str):
        self.view.progress.setVisible(False)
        self.view.status_label.setText(f"Saved: {date_str}")
        self.refresh_grid()

    def refresh_grid(self):
        for i in reversed(range(self.view.grid_layout.count())): 
            item = self.view.grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        db = self.model.db["photos"]
        sorted_dates = sorted(db.keys())
        self.sorted_ids = [db[d] for d in sorted_dates]

        row, col = 0, 0
        for date in sorted_dates:
            file_id = db[date]
            proxy_path = os.path.join(self.model.dirs["proxies"], f"{file_id}.jpg")
            if os.path.exists(proxy_path):
                pix = QPixmap(proxy_path)
                self.view.add_photo_to_grid(pix, date, row, col, file_id)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
        
        self.view.heatmap.set_data(self.model.db["photos"])

    

    def open_export_dialog(self):
        self.export_dlg = ExportDialog(self.view)
        self.export_dlg.export_requested.connect(self.start_export)
        self.export_dlg.exec()

    def start_export(self, audio_path, preset, fps, is_split):
        output_path, _ = QFileDialog.getSaveFileName(self.view, "Save Video", "my_timelapse.mp4", "MP4 Video (*.mp4)")
        if not output_path:
            self.export_dlg.btn_export.setEnabled(True)
            return

        
        photos = [os.path.join(self.model.dirs["proxies"], f"{fid}.jpg") for fid in self.sorted_ids]
        if not photos: return

        
        self.render_thread = QThread()
        
        self.render_worker = RenderWorker(output_path, photos, audio_path, fps, is_split)
        self.render_worker.moveToThread(self.render_thread)
        
        self.render_worker.progress.connect(self.export_dlg.update_progress)
        self.render_worker.finished.connect(self.on_export_finished)
        self.render_thread.started.connect(self.render_worker.run)
        
        self.render_worker.finished.connect(self.render_thread.quit)
        self.render_worker.finished.connect(self.render_worker.deleteLater)
        self.render_thread.finished.connect(self.render_thread.deleteLater)
        
        self.render_thread.start()

    def on_export_finished(self, success):
        self.export_dlg.export_finished()
        if success:
            QMessageBox.information(self.view, "Success", "Video exported successfully!")
        else:
            QMessageBox.critical(self.view, "Error", "Video render failed. Check terminal for details.")

    
    def enter_editor(self, file_id):
        self.current_editing_id = file_id
        active_path = os.path.join(self.model.dirs["proxies"], f"{file_id}.jpg")
        ghost_path = None
        if file_id in self.sorted_ids:
            idx = self.sorted_ids.index(file_id)
            if idx > 0:
                prev_id = self.sorted_ids[idx - 1]
                ghost_path = os.path.join(self.model.dirs["proxies"], f"{prev_id}.jpg")

        self.view.editor.load_images(active_path, ghost_path)
        
        if ghost_path:
            with Image.open(ghost_path) as img:
                w, h = img.size
            landmarks = self.ai_pose.get_landmarks(ghost_path)
            if landmarks:
                self.view.editor.draw_skeleton(landmarks, w, h)
                self.view.editor.chk_skeleton.setChecked(True)
            else:
                self.view.editor.chk_skeleton.setChecked(False)
        self.view.stack.setCurrentIndex(1)

    def exit_editor(self):
        self.view.stack.setCurrentIndex(0)
        self.refresh_grid()

    def rotate_image(self):
        if not self.current_editing_id: return
        path = os.path.join(self.model.dirs["proxies"], f"{self.current_editing_id}.jpg")
        cmd = RotateCommand(path, -90)
        self.invoker.execute_command(cmd)
        self.view.editor.refresh_active(path)

    def undo_action(self):
        if not self.current_editing_id: return
        self.invoker.undo()
        path = os.path.join(self.model.dirs["proxies"], f"{self.current_editing_id}.jpg")
        self.view.editor.refresh_active(path)

    def run_auto_align(self):
        if not self.current_editing_id: return
        path = os.path.join(self.model.dirs["proxies"], f"{self.current_editing_id}.jpg")
        cmd = AutoAlignCommand(path)
        self.invoker.execute_command(cmd)
        self.view.editor.refresh_active(path)

    def run_deflicker(self):
        if not self.current_editing_id: return
        path = os.path.join(self.model.dirs["proxies"], f"{self.current_editing_id}.jpg")
        ghost_path = None
        if self.current_editing_id in self.sorted_ids:
            idx = self.sorted_ids.index(self.current_editing_id)
            if idx > 0:
                prev_id = self.sorted_ids[idx - 1]
                ghost_path = os.path.join(self.model.dirs["proxies"], f"{prev_id}.jpg")

        if ghost_path:
            cmd = DeflickerCommand(path, ghost_path)
            self.invoker.execute_command(cmd)
            self.view.editor.refresh_active(path)

    def run_gap_fill(self):
        if not self.current_editing_id: return
        if not self.sorted_ids: return
        try: idx = self.sorted_ids.index(self.current_editing_id)
        except ValueError: return
        if idx >= len(self.sorted_ids) - 1: return
        next_id = self.sorted_ids[idx + 1]

        cmd = GenerateGapFillCommand(self.current_editing_id, next_id, self.model.dirs)
        new_id = cmd.execute() 
        if new_id:
            current_date_key = [k for k, v in self.model.db["photos"].items() if v == self.current_editing_id][0]
            try:
                dt = datetime.strptime(current_date_key, "%Y-%m-%d %H-%M-%S")
                new_dt = dt + timedelta(hours=12)
                new_date_str = new_dt.strftime("%Y-%m-%d %H-%M-%S")
                self.model.db["photos"][new_date_str] = new_id
                self.model._save_db()
            except Exception as e:
                print(f"DB Update Error: {e}")