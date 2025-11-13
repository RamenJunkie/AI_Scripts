# WordPress Image Optimizer

A shell script to automatically optimize and resize images in your WordPress media library.

## Features

- 🔍 Recursively scans all subdirectories for images (JPG, PNG, GIF)
- 📏 Resizes images larger than 2048px (maintains aspect ratio)
- 🗜️ Compresses images for optimal file size
- ⚡ Skips images with minimal savings (<1%)
- 📊 Provides detailed statistics (before/after sizes, space saved)
- 📝 Logs errors to a separate file
- 🎨 Color-coded console output

## Installation

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install imagemagick jpegoptim optipng gifsicle
```

### macOS

```bash
brew install imagemagick jpegoptim optipng gifsicle
```

## Usage

1. Make the script executable:
```bash
chmod +x optimize-images.sh
```

2. Navigate to your WordPress uploads directory:
```bash
cd /var/www/html/wp-content/uploads
```

3. Run the script:
```bash
./optimize-images.sh
```

## Output

The script will display:
- Real-time progress for each image
- Total images found and processed
- Number of images resized
- Before/after directory sizes
- Total space saved

Any errors are logged to `image_optimization_errors.log`

## Configuration

You can modify these settings in the script:
- `MAX_DIMENSION`: Maximum width/height (default: 2048px)
- `MIN_SAVINGS_PERCENT`: Minimum savings to process (default: 1%)

## Safety

- Creates temporary files during processing
- Only overwrites originals if optimization succeeds
- Validates images before processing
- Provides detailed error logging

## Example Output

```
========================================
WordPress Image Optimization Script
========================================

✓ Optimized: photo1.jpg (saved: 245.32KB, 35%)
↔ Resized: large-image.png (3200x2400 → max 2048px)
○ Skipped: logo.png (minimal savings: 0%)

========================================
OPTIMIZATION COMPLETE
========================================

Images Found:        156
Images Processed:    142
Images Resized:      8
Images Skipped:      12
Errors:              2

Size Before:         125.67MB
Size After:          89.23MB
Total Saved:         36.44MB (29%)
========================================
```