import cv2
import numpy as np
from PIL import Image

class ImageProcessor:
    @staticmethod
    def match_histograms(source_path, reference_path):
        """
        Adjusts the brightness/contrast of 'source' to match 'reference'.
        Returns: A PIL Image object (corrected).
        """
        try:
            
            src = cv2.imread(source_path)
            ref = cv2.imread(reference_path)
            
            if src is None or ref is None:
                return None

            
            
            
            src_yuv = cv2.cvtColor(src, cv2.COLOR_BGR2YUV)
            ref_yuv = cv2.cvtColor(ref, cv2.COLOR_BGR2YUV)

            
            src_y, src_u, src_v = cv2.split(src_yuv)
            ref_y, ref_u, ref_v = cv2.split(ref_yuv)

            
            
            
            
            src_mean, src_std = cv2.meanStdDev(src_y)
            ref_mean, ref_std = cv2.meanStdDev(ref_y)

            
            src_m, src_s = src_mean[0][0], src_std[0][0]
            ref_m, ref_s = ref_mean[0][0], ref_std[0][0]

            
            if src_s == 0: src_s = 1.0

            
            
            result_y = (src_y.astype(float) - src_m) * (ref_s / src_s) + ref_m
            
            
            result_y = np.clip(result_y, 0, 255).astype(np.uint8)

            
            result_yuv = cv2.merge([result_y, src_u, src_v])
            result_bgr = cv2.cvtColor(result_yuv, cv2.COLOR_YUV2BGR)

            
            
            result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
            return Image.fromarray(result_rgb)

        except Exception as e:
            print(f"Deflicker Error: {e}")
            return None