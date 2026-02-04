import numpy as np
import cv2
import math
from PIL import Image

# --- SAFE IMPORT BLOCK ---
try:
    import mediapipe as mp
    if not hasattr(mp, 'solutions'):
        raise ImportError("MediaPipe broken")
    HAS_AI = True
except:
    HAS_AI = False

class PoseDetector:
    def __init__(self):
        self.face_mesh = None
        self.pose = None
        
        # 1. Try to load AI Models
        if HAS_AI:
            try:
                # Load Face Mesh (For Auto-Align)
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5
                )
                
                # Load Pose (For Skeleton Guide)
                self.mp_pose = mp.solutions.pose
                self.pose = self.mp_pose.Pose(
                    static_image_mode=True,
                    model_complexity=1,
                    min_detection_confidence=0.5
                )
            except:
                print("⚠️ AI Init Failed. Falling back to OpenCV.")

        # 2. Load OpenCV Classifiers (The Backup)
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    # --- PHASE 3: SKELETON GUIDE (Restored) ---
    def get_landmarks(self, image_path):
        """
        Returns list of (x,y) for body skeleton.
        Used by the Green Wireframe feature.
        """
        if not self.pose: return None
        
        try:
            pil_img = Image.open(image_path).convert('RGB')
            np_img = np.array(pil_img)
            results = self.pose.process(np_img)
            
            if not results.pose_landmarks:
                return None
                
            landmarks = []
            for lm in results.pose_landmarks.landmark:
                landmarks.append((lm.x, lm.y))
            return landmarks
        except Exception as e:
            print(f"Skeleton AI Error: {e}")
            return None

    # --- PHASE 4: AUTO-ALIGN ---
    def get_eye_angle(self, image_path):
        """
        Returns angle to rotate face so eyes are horizontal.
        """
        # Try AI First
        if self.face_mesh:
            angle = self._get_angle_ai(image_path)
            if angle is not None: return angle

        # Fallback to OpenCV
        return self._get_angle_opencv(image_path)

    def _get_angle_ai(self, image_path):
        try:
            pil_img = Image.open(image_path).convert('RGB')
            np_img = np.array(pil_img)
            results = self.face_mesh.process(np_img)

            if not results.multi_face_landmarks:
                return None

            lm = results.multi_face_landmarks[0].landmark
            
            # Left Eye (33), Right Eye (263)
            left_eye = (lm[33].x, lm[33].y)
            right_eye = (lm[263].x, lm[263].y)
            
            return self._calculate_angle(left_eye, right_eye)
        except:
            return None

    def _get_angle_opencv(self, image_path):
        try:
            img = cv2.imread(image_path)
            if img is None: return None
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            eyes = self.eye_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(eyes) < 2: return None 

            eyes = sorted(eyes, key=lambda x: x[0])
            e1 = eyes[0]
            e2 = eyes[-1] 
            
            pt1 = (e1[0] + e1[2]/2, e1[1] + e1[3]/2)
            pt2 = (e2[0] + e2[2]/2, e2[1] + e2[3]/2)
            
            h, w = img.shape[:2]
            pt1_norm = (pt1[0]/w, pt1[1]/h)
            pt2_norm = (pt2[0]/w, pt2[1]/h)
            
            return self._calculate_angle(pt1_norm, pt2_norm)
        except Exception as e:
            print(f"OpenCV Error: {e}")
            return None

    def _calculate_angle(self, point_a, point_b):
        dx = point_b[0] - point_a[0]
        dy = point_b[1] - point_a[1]
        angle_rad = math.atan2(dy, dx)
        return math.degrees(angle_rad)