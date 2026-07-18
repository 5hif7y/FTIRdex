import os
from PIL import Image

def main():
    # Look for icon.jpg in project root or current folder
    src_paths = [
        os.path.join("..", "assets", "icon.png"),
        os.path.join("..", "assets", "icon.jpg"),
        os.path.join("assets", "icon.png"),
        os.path.join("assets", "icon.jpg"),
        os.path.join("..", "icon.png"),
        os.path.join("..", "icon.jpg"),
        "icon.png",
        "icon.jpg",
        os.path.join(".", "icon.png"),
        os.path.join(".", "icon.jpg")
    ]
    
    src_path = None
    for p in src_paths:
        if os.path.exists(p):
            src_path = p
            break
            
    if not src_path:
        print("Error: Could not find icon.jpg in root or current directory.")
        return
        
    try:
        img = Image.open(src_path)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
            
        dest_path = "icon.ico"
        # Compile multi-resolution icon sizes: 16x16, 32x32, 48x48, 256x256
        img.save(dest_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
        print(f"Successfully generated local Windows icon '{dest_path}' from '{src_path}'!")
    except Exception as e:
        print(f"Error compiling icon: {e}")

if __name__ == "__main__":
    main()
