import os

from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, clips_array
from PIL import Image

class VideoRenderer:
    def __init__(self, export_path, photo_paths, audio_path=None, beat_schedule=None, fps=30, split_screen=False):
        self.export_path = export_path
        self.photo_paths = photo_paths
        self.audio_path = audio_path
        self.beat_schedule = beat_schedule
        self.fps = fps
        self.split_screen = split_screen 
        self.use_gpu = False 

    def render(self, progress_callback=None):
        clips = []
        total_photos = len(self.photo_paths)

        if total_photos == 0: return False

        try:
            
            for i, path in enumerate(self.photo_paths):
                duration = 0.1 
                
                if self.beat_schedule and i < len(self.beat_schedule) - 1:
                    start_time = self.beat_schedule[i]
                    end_time = self.beat_schedule[i+1]
                    duration = end_time - start_time
                else:
                    duration = 1.0 / 10 
                
                if duration < 0.04: duration = 0.04 

                clip = ImageClip(path).set_duration(duration)
                clips.append(clip)

                if progress_callback:
                    progress_callback(int((i / total_photos) * 40)) 

            
            main_video = concatenate_videoclips(clips, method="compose")

            
            final_video = main_video
            
            if self.split_screen and total_photos > 0:
                
                
                first_photo_path = self.photo_paths[0]
                static_start = ImageClip(first_photo_path).set_duration(main_video.duration)
                
                
                
                
                final_video = clips_array([[static_start, main_video]])
            

            
            if self.audio_path:
                try:
                    audio = AudioFileClip(self.audio_path)
                    if audio.duration < final_video.duration:
                         pass 
                    else:
                        audio = audio.subclip(0, final_video.duration)
                    
                    final_video = final_video.set_audio(audio)
                except Exception as e:
                    print(f"Audio Merge Error: {e}")

            
            if progress_callback: progress_callback(60)
            
            final_video.write_videofile(
                self.export_path, 
                fps=self.fps, 
                codec='libx264', 
                audio_codec='aac',
                preset='medium', 
                threads=4 
            )
            
            if progress_callback: progress_callback(100)
            return True

        except Exception as e:
            print(f"Render Error: {e}")
            return False