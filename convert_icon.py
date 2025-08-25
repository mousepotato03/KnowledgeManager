#!/usr/bin/env python3
"""
Convert PNG/JPG image to ICO format for Windows shortcut icons
"""

import os

def convert_to_ico(input_file, output_file, sizes=None):
    """Convert image file to ICO format"""
    try:
        from PIL import Image
        
        if sizes is None:
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Open the image
        img = Image.open(input_file)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create different sized versions with better quality
        icon_images = []
        
        # For better quality, use high-quality resampling and preserve original if it's good size
        original_size = img.size
        print(f"Original image size: {original_size}")
        
        # If original is good size, use it directly for some sizes
        for size in sizes:
            if original_size == size:
                # Use original directly if size matches
                icon_images.append(img)
                print(f"Using original quality for {size}")
            else:
                # Use high-quality resampling
                resized = img.resize(size, Image.Resampling.LANCZOS)
                icon_images.append(resized)
                print(f"Resized to {size}")
        
        # Save as ICO with all sizes
        icon_images[0].save(
            output_file, 
            format='ICO', 
            sizes=[img.size for img in icon_images],
            append_images=icon_images[1:] if len(icon_images) > 1 else None
        )
        print(f"Successfully converted {input_file} to {output_file}")
        return True
        
    except ImportError:
        print("PIL (Pillow) not installed. Installing...")
        import subprocess
        import sys
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
            print("Pillow installed successfully!")
            print("Please run the conversion again.")
            return False
        except Exception as e:
            print(f"Failed to install Pillow: {e}")
            return False
            
    except Exception as e:
        print(f"Error converting icon: {e}")
        return False

# Main execution
if __name__ == "__main__":
    # Check for different possible icon files
    possible_files = ["icon.jpg", "icon.png", "icon.png.jpg", "icon.jpeg"]
    input_file = None
    
    for file in possible_files:
        if os.path.exists(file):
            input_file = file
            print(f"Found icon file: {file}")
            break
    
    if input_file:
        output_file = "icon.ico"
        if convert_to_ico(input_file, output_file):
            print(f"Icon ready for use: {output_file}")
        else:
            print("Fallback: Using system icon instead")
    else:
        print(f"No icon file found. Tried: {', '.join(possible_files)}")
        print("Using system icon instead")