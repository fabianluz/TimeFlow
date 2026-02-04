from abc import ABC, abstractmethod
from PIL import Image
import os
import uuid
from app.model.ai_pose import PoseDetector
from app.model.image_processor import ImageProcessor

class Command(ABC):
    """The blueprint for any action in the editor."""
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

class CommandInvoker:
    """The History Manager (The 'Time Machine')."""
    def __init__(self):
        self.history = [] # Stack of executed commands
        self.redo_stack = []

    def execute_command(self, command):
        command.execute()
        self.history.append(command)
        self.redo_stack.clear() # Clear redo history on new action

    def undo(self):
        if not self.history:
            return
        command = self.history.pop()
        command.undo()
        self.redo_stack.append(command)

    def redo(self):
        if not self.redo_stack:
            return
        command = self.redo_stack.pop()
        command.execute()
        self.history.append(command)

# --- CONCRETE COMMANDS ---

class RotateCommand(Command):
    def __init__(self, file_path, angle):
        self.path = file_path
        self.angle = angle

    def execute(self):
        self._rotate(self.angle)

    def undo(self):
        # For simple 90 degree rotations, mathematical undo is safe
        self._rotate(-self.angle)

    def _rotate(self, angle):
        try:
            with Image.open(self.path) as img:
                rotated = img.rotate(angle, expand=True)
                rotated.save(self.path, quality=95)
        except Exception as e:
            print(f"Rotate Error: {e}")

class AutoAlignCommand(Command):
    def __init__(self, file_path):
        self.path = file_path
        self.detector = PoseDetector()
        self.backup = None # Snapshot storage

    def execute(self):
        # 1. Take a Snapshot BEFORE changing anything
        try:
            with Image.open(self.path) as img:
                self.backup = img.copy()
        except Exception as e:
            print(f"Backup failed: {e}")
            return

        # 2. Calculate Angle
        current_angle = self.detector.get_eye_angle(self.path)
        
        if current_angle is not None:
            # 3. Apply Correction
            correction = -current_angle
            print(f"Auto-Align: Correcting by {correction:.2f} degrees")
            self._rotate(correction)
        else:
            print("Auto-Align: No eyes detected.")

    def undo(self):
        # Restore the snapshot
        if self.backup:
            try:
                self.backup.save(self.path, quality=95)
                print("Auto-Align undone.")
            except Exception as e:
                print(f"Undo Error: {e}")

    def _rotate(self, angle):
        with Image.open(self.path) as img:
            # expand=False keeps the image size same (important for alignment)
            rotated = img.rotate(angle, expand=False, resample=Image.BICUBIC)
            rotated.save(self.path, quality=95)

class DeflickerCommand(Command):
    def __init__(self, active_path, reference_path):
        self.active = active_path
        self.ref = reference_path
        self.backup = None # Snapshot storage

    def execute(self):
        # 1. Take a Snapshot
        try:
            with Image.open(self.active) as img:
                self.backup = img.copy()
        except Exception as e:
            print(f"Backup failed: {e}")
            return

        # 2. Apply Deflicker
        corrected_img = ImageProcessor.match_histograms(self.active, self.ref)
        if corrected_img:
            corrected_img.save(self.active, quality=95)
            print("Deflicker applied.")

    def undo(self):
        # Restore the snapshot
        if self.backup:
            try:
                self.backup.save(self.active, quality=95)
                print("Deflicker undone.")
            except Exception as e:
                print(f"Undo Error: {e}")

class GenerateGapFillCommand(Command):
    def __init__(self, current_id, next_id, model_dirs):
        self.current_id = current_id
        self.next_id = next_id
        self.dirs = model_dirs
        self.generated_file_path = None

    def execute(self):
        path_a = os.path.join(self.dirs["proxies"], f"{self.current_id}.jpg")
        path_b = os.path.join(self.dirs["proxies"], f"{self.next_id}.jpg")
        
        try:
            img_a = Image.open(path_a).convert("RGB")
            img_b = Image.open(path_b).convert("RGB")
            
            if img_a.size != img_b.size:
                img_b = img_b.resize(img_a.size, Image.Resampling.LANCZOS)

            # Simple 50% opacity blend
            result = Image.blend(img_a, img_b, 0.5)

            new_id = str(uuid.uuid4())
            self.generated_file_path = os.path.join(self.dirs["proxies"], f"{new_id}.jpg")
            
            result.save(self.generated_file_path, quality=90)
            return new_id

        except Exception as e:
            print(f"Gap Fill Error: {e}")
            return None

    def undo(self):
        if self.generated_file_path and os.path.exists(self.generated_file_path):
            os.remove(self.generated_file_path)
            print("Gap Fill Undone (File Deleted)")