#!/usr/bin/env python3
"""
Generate placeholder app icons for Android Health Monitor
Creates simple PNG icons with a health/heart theme
"""

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not available. Will create minimal placeholder files.")

import os

# Icon sizes for different densities
ICON_SIZES = {
    'mdpi': 48,
    'hdpi': 72,
    'xhdpi': 96,
    'xxhdpi': 144,
    'xxxhdpi': 192
}

BASE_PATH = 'app/src/main/res'

def create_icon_with_pil(size, output_path):
    """Create a health-themed icon using PIL"""
    # Create image with green background
    img = Image.new('RGB', (size, size), color='#3DDC84')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple heart shape (simplified)
    center_x, center_y = size // 2, size // 2
    heart_size = size // 3
    
    # Draw white circle as simplified heart/health icon
    draw.ellipse(
        [center_x - heart_size, center_y - heart_size,
         center_x + heart_size, center_y + heart_size],
        fill='white'
    )
    
    # Draw red cross/plus sign
    cross_width = size // 8
    cross_length = size // 2
    draw.rectangle(
        [center_x - cross_width, center_y - cross_length,
         center_x + cross_width, center_y + cross_length],
        fill='#FF5252'
    )
    draw.rectangle(
        [center_x - cross_length, center_y - cross_width,
         center_x + cross_length, center_y + cross_width],
        fill='#FF5252'
    )
    
    img.save(output_path, 'PNG')
    print(f"Created: {output_path}")

def create_minimal_png(size, output_path):
    """Create a minimal valid PNG file without PIL"""
    # This creates a tiny valid PNG (1x1 pixel) that Android will accept
    # It's not pretty but it will allow the build to succeed
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde'  # IHDR chunk
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05'
        b'\x18\r\n\x1d'  # IDAT chunk
        b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND chunk
    )
    
    with open(output_path, 'wb') as f:
        f.write(png_data)
    print(f"Created minimal PNG: {output_path}")

def main():
    print("Generating Android app icons...")
    print(f"PIL available: {PIL_AVAILABLE}")
    
    for density, size in ICON_SIZES.items():
        mipmap_dir = os.path.join(BASE_PATH, f'mipmap-{density}')
        os.makedirs(mipmap_dir, exist_ok=True)
        
        for icon_name in ['ic_launcher.png', 'ic_launcher_round.png']:
            output_path = os.path.join(mipmap_dir, icon_name)
            
            if PIL_AVAILABLE:
                create_icon_with_pil(size, output_path)
            else:
                create_minimal_png(size, output_path)
    
    print("\n✓ Icon generation complete!")
    if not PIL_AVAILABLE:
        print("\nNote: Minimal placeholder icons were created.")
        print("For better icons, install Pillow: pip install Pillow")
        print("Then run this script again.")

if __name__ == '__main__':
    main()
