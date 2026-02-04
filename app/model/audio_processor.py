import librosa
import numpy as np
import os

class AudioProcessor:
    def __init__(self):
        self.audio_path = None
        self.beat_times = []
        self.duration = 0

    def load_audio(self, file_path):
        """
        Loads an audio file and detects beats.
        Returns: (duration_in_seconds, estimated_tempo)
        """
        try:
            self.audio_path = file_path
            
            # 1. Load the audio file (sr=None preserves native sampling rate)
            # This can be slow for long songs, so we warn the user in UI
            y, sr = librosa.load(file_path, sr=None)
            self.duration = librosa.get_duration(y=y, sr=sr)
            
            # 2. Separate harmonic (music) and percussive (drums) signals
            # Beats are easiest to find in the percussive layer
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            # 3. Detect Tempo and Beat Frames
            tempo, beat_frames = librosa.beat.beat_track(y=y_percussive, sr=sr)
            
            # 4. Convert Frame indices to Time (seconds)
            self.beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # Ensure the first beat starts at 0 or close to it
            if len(self.beat_times) > 0 and self.beat_times[0] > 1.0:
               self.beat_times = np.insert(self.beat_times, 0, 0.0)

            return self.duration, tempo

        except Exception as e:
            print(f"Audio Error: {e}")
            return 0, 0

    def get_sync_schedule(self, num_photos):
        """
        Matches photos to beats.
        If we have 10 photos but 50 beats, we pick every 5th beat.
        If we have 50 photos but 10 beats, we are in trouble (images will be too fast).
        """
        if not self.beat_times.any():
            return []

        # Simple Logic: One photo per beat
        # If there are more beats than photos, just use the first N beats
        schedule = list(self.beat_times[:num_photos])
        
        # If we run out of beats but have more photos, append fixed duration
        if len(schedule) < num_photos:
            last_time = schedule[-1] if schedule else 0
            avg_gap = 0.5 # Default 0.5s per photo if no beats left
            
            remaining = num_photos - len(schedule)
            for _ in range(remaining):
                last_time += avg_gap
                schedule.append(last_time)
                
        return schedule