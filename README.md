# TimeFlow ⏳
A professional-grade desktop application for macOS (Apple Silicon) designed to create perfect daily-photo transition videos.

## Features
- **AI-Powered Alignment:** Automatic face detection and rotation using MediaPipe and OpenCV.
- **Smart Deflicker:** Histogram matching to normalize exposure between days.
- **Audio-Reactive Export:** Automatically syncs photo transitions to the beats of an MP3.
- **Split-Screen Mode:** Compare "Day 1" vs "Current Day" side-by-side in the final export.
- **Ghost Mode:** Semi-transparent overlays for manual alignment.

## Tech Stack
- **UI:** PyQt6 with a custom macOS-native aesthetic.
- **Processing:** Pillow, OpenCV, and Librosa.
- **Video:** MoviePy.
