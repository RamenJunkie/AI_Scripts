#!/bin/bash

# Zine Image Processor with Fixed Crop Dimensions
# Crops bottom 75px, then processes based on position (first/last vs middle)
# Specifically used for cropping and splitting 2 page screen shots of Zine Pages, Could be used to process other images ie books.

set -e

# Configuration
BOTTOM_CROP=75
NARROW_WIDTH=690
NARROW_HEIGHT=980
WIDE_WIDTH=1380
WIDE_HEIGHT=980
TEMP_DIR="processed_temp"

process_folder() {
    local folder="$1"
    local folder_name=$(basename "$folder")
    
    echo "Processing folder: $folder_name"
    
    # Get all image files sorted by modification time
    mapfile -t images < <(find "$folder" -maxdepth 1 -type f \
        \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) \
        -printf "%T@ %p\n" | sort -n | cut -d' ' -f2-)
    
    if [ ${#images[@]} -eq 0 ]; then
        echo "  No images found in $folder_name"
        return
    fi
    
    local total_images=${#images[@]}
    local page_num=1
    
    echo "  Found $total_images image(s)"
    
    for idx in "${!images[@]}"; do
        local img="${images[$idx]}"
        local img_name=$(basename "$img")
        
        # Get original dimensions
        local orig_width=$(identify -format "%w" "$img")
        local orig_height=$(identify -format "%h" "$img")
        
        echo "  Processing [$((idx + 1))/$total_images]: $img_name (${orig_width}x${orig_height})"
        
        # First, crop bottom 75 pixels
        local cropped_height=$((orig_height - BOTTOM_CROP))
        local temp_cropped=$(mktemp --suffix=.jpg)
        convert "$img" -gravity North -crop ${orig_width}x${cropped_height}+0+0 +repage "$temp_cropped"
        
        # Determine if this is first, last, or middle image
        if [ "$idx" -eq 0 ] || [ "$idx" -eq $((total_images - 1)) ]; then
            # First or last image - crop to narrow page (690x980) centered
            echo "    Type: Cover page (narrow)"
            local output=$(printf "%s/%s - Page %02d.jpg" "$folder" "$folder_name" $page_num)
            convert "$temp_cropped" -gravity Center -crop ${NARROW_WIDTH}x${NARROW_HEIGHT}+0+0 +repage "$output"
            echo "    Created: $(basename "$output")"
            page_num=$((page_num + 1))
        else
            # Middle image - crop to wide (1380x980) centered, then split
            echo "    Type: Interior spread (wide, will split)"
            
            # Crop to wide dimensions centered
            local temp_wide=$(mktemp --suffix=.jpg)
            convert "$temp_cropped" -gravity Center -crop ${WIDE_WIDTH}x${WIDE_HEIGHT}+0+0 +repage "$temp_wide"
            
            # Split into left and right halves
            local half_width=$((WIDE_WIDTH / 2))
            
            # Left page
            local output_left=$(printf "%s/%s - Page %02d.jpg" "$folder" "$folder_name" $page_num)
            convert "$temp_wide" -crop ${half_width}x${WIDE_HEIGHT}+0+0 +repage "$output_left"
            echo "    Created: $(basename "$output_left") (left)"
            page_num=$((page_num + 1))
            
            # Right page
            local output_right=$(printf "%s/%s - Page %02d.jpg" "$folder" "$folder_name" $page_num)
            convert "$temp_wide" -crop ${half_width}x${WIDE_HEIGHT}+${half_width}+0 +repage "$output_right"
            echo "    Created: $(basename "$output_right") (right)"
            page_num=$((page_num + 1))
            
            rm "$temp_wide"
        fi
        
        rm "$temp_cropped"
    done
    
    # Create PDF from processed images
    echo "  Creating PDF..."
    local pdf_output="$folder/${folder_name}.pdf"
    convert "$folder/${folder_name} - Page"*.jpg "$pdf_output"
    echo "  Created: ${folder_name}.pdf"
    
    echo "  Completed: $folder_name ($((page_num - 1)) pages)"
    echo ""
}

# Main execution
main() {
    if [ $# -eq 0 ]; then
        echo "Usage: $0 <directory>"
        echo "Processes all image folders recursively from the given directory"
        exit 1
    fi
    
    local base_dir="$1"
    
    if [ ! -d "$base_dir" ]; then
        echo "Error: Directory '$base_dir' does not exist"
        exit 1
    fi
    
    # Check for required tools
    for cmd in convert identify; do
        if ! command -v $cmd &> /dev/null; then
            echo "Error: Required command '$cmd' not found"
            echo "Please install ImageMagick"
            exit 1
        fi
    done
    
    echo "Starting zine processing..."
    echo "Config: Bottom crop=${BOTTOM_CROP}px, Narrow=${NARROW_WIDTH}x${NARROW_HEIGHT}, Wide=${WIDE_WIDTH}x${WIDE_HEIGHT}"
    echo ""
    
    # Find all directories containing images
    while IFS= read -r -d '' folder; do
        # Check if folder contains images
        if find "$folder" -maxdepth 1 -type f \
            \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) \
            | grep -q .; then
            process_folder "$folder"
        fi
    done < <(find "$base_dir" -type d -print0)
    
    echo "All processing complete!"
}

main "$@"
