from PIL import Image 
from pathlib import Path

def open_image(path: Path)->Image.Image:
    with Image.open(path) as f:
        return f.copy()    # A little bit eh

def save_image(path: Path, img:Image.Image)->None:
    img.save(path)


