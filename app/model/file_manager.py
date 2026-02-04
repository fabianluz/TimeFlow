import os
import shutil
import uuid
import json
from datetime import datetime
from PIL import Image, ImageOps, ExifTags
from pillow_heif import register_heif_opener

register_heif_opener()

class FileManager:
    def __init__(self, root_path):
        self.root_path = root_path
        self.dirs = {
            "originals": os.path.join(root_path, "originals"),
            "proxies": os.path.join(root_path, "proxies"),
            "data": os.path.join(root_path, "data"), 
        }
        self.db_path = os.path.join(self.dirs["data"], "project.json")
        self._init_folders()
        self.db = self._load_db()

    def _init_folders(self):
        for path in self.dirs.values():
            os.makedirs(path, exist_ok=True)

    def _load_db(self):
        """Loads the project database or creates a new one."""
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {"photos": {}} 

    def _save_db(self):
        """Saves memory state to JSON file."""
        with open(self.db_path, 'w') as f:
            json.dump(self.db, f, indent=4)

    def ingest_photo(self, file_path):
        file_id = str(uuid.uuid4())
        
        
        ext = os.path.splitext(file_path)[1].lower()
        original_dest = os.path.join(self.dirs["originals"], f"{file_id}{ext}")
        shutil.copy2(file_path, original_dest)

        
        date_str = self._get_date_taken(original_dest)
        
        
        proxy_dest = os.path.join(self.dirs["proxies"], f"{file_id}.jpg")
        self._create_proxy(original_dest, proxy_dest)
        
        
        if date_str:
            self.db["photos"][date_str] = file_id
            self._save_db()
            
        return file_id, date_str

    def _get_date_taken(self, path):
        """Extracts EXIF Date or returns Today+UniqueTime if missing."""
        
        default_unique = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        
        try:
            with Image.open(path) as img:
                exif = img.getexif()
                if not exif: 
                    return default_unique
                
                
                date_str = exif.get(36867) 
                if date_str:
                    
                    dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    
                    return dt.strftime("%Y-%m-%d %H-%M-%S")
        except Exception as e:
            print(f"Date Error: {e}")
        
        return default_unique

    def _create_proxy(self, input_path, output_path):
            try:
                with Image.open(input_path) as img:
                    img = ImageOps.exif_transpose(img)
                    
                    
                    if img.mode in ("RGBA", "P"): 
                        img = img.convert("RGB")
                    

                    img.thumbnail((500, 500))
                    img.save(output_path, "JPEG", quality=80)
            except Exception as e:
                print(f"Proxy Error: {e}")