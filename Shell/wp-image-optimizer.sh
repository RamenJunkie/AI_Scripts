#!/bin/bash

# WordPress Image Optimization Script
# Recursively optimizes JPG, PNG, and GIF images
# Resizes images larger than 2048px and compresses them

set -eo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_DIMENSION=2048
MIN_SAVINGS_PERCENT=1  # Skip if savings are less than 1%
ERROR_LOG="image_optimization_errors.log"

# Statistics variables
total_images=0
processed_images=0
skipped_images=0
resized_images=0
error_count=0
total_size_before=0
total_size_after=0

# Clear error log
> "$ERROR_LOG"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}WordPress Image Optimization Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for required tools
check_dependencies() {
    local missing_deps=()
    
    command -v convert >/dev/null 2>&1 || missing_deps+=("imagemagick")
    command -v jpegoptim >/dev/null 2>&1 || missing_deps+=("jpegoptim")
    command -v optipng >/dev/null 2>&1 || missing_deps+=("optipng")
    command -v gifsicle >/dev/null 2>&1 || missing_deps+=("gifsicle")
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing required dependencies:${NC}"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        echo "Install on Ubuntu/Debian:"
        echo "  sudo apt-get install imagemagick jpegoptim optipng gifsicle"
        echo ""
        echo "Install on macOS:"
        echo "  brew install imagemagick jpegoptim optipng gifsicle"
        exit 1
    fi
}

# Function to get file size in bytes
get_file_size() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        stat -f%z "$1"
    else
        stat -c%s "$1"
    fi
}

# Function to format bytes to human readable
format_bytes() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes}B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1024}")KB"
    elif [ $bytes -lt 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1048576}")MB"
    else
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1073741824}")GB"
    fi
}

# Function to process an image
process_image() {
    local file="$1"
    local filename=$(basename "$file")
    
    # Debug: Show we're processing
    if [ $total_images -eq 0 ]; then
        echo "Starting first image..."
    fi
    
    total_images=$((total_images + 1))
    
    # Get original size
    local size_before=$(get_file_size "$file")
    total_size_before=$((total_size_before + size_before))
    
    # Get image dimensions
    local dimensions=$(identify -format "%w %h" "$file" 2>/dev/null || echo "0 0")
    local width=$(echo $dimensions | cut -d' ' -f1)
    local height=$(echo $dimensions | cut -d' ' -f2)
    
    if [ "$width" = "0" ] || [ "$height" = "0" ]; then
        echo -e "${RED}✗${NC} Error reading: $file"
        echo "$file - Unable to read image dimensions" >> "$ERROR_LOG"
        error_count=$((error_count + 1))
        total_size_after=$((total_size_after + size_before))
        return
    fi
    
    local needs_resize=false
    
    # Check if resize is needed
    if [ "$width" -gt "$MAX_DIMENSION" ] || [ "$height" -gt "$MAX_DIMENSION" ]; then
        needs_resize=true
    fi
    
    # Create a temporary file for processing
    local temp_file="${file}.tmp"
    cp "$file" "$temp_file"
    
    # Resize if needed
    if [ "$needs_resize" = true ]; then
        if convert "$temp_file" -resize "${MAX_DIMENSION}x${MAX_DIMENSION}>" "$temp_file" 2>/dev/null; then
            resized_images=$((resized_images + 1))
            echo -e "${YELLOW}↔${NC} Resized: $filename (${width}x${height} → max ${MAX_DIMENSION}px)"
        else
            echo -e "${RED}✗${NC} Resize error: $file"
            echo "$file - Resize failed" >> "$ERROR_LOG"
            error_count=$((error_count + 1))
            rm -f "$temp_file"
            total_size_after=$((total_size_after + size_before))
            return
        fi
    fi
    
    # Compress based on file type
    local extension="${file##*.}"
    extension=$(echo "$extension" | tr '[:upper:]' '[:lower:]')
    
    case "$extension" in
        jpg|jpeg)
            if ! jpegoptim --strip-all --max=85 "$temp_file" >/dev/null 2>&1; then
                echo -e "${RED}✗${NC} Compression error: $file"
                echo "$file - JPEG compression failed" >> "$ERROR_LOG"
                error_count=$((error_count + 1))
                rm -f "$temp_file"
                total_size_after=$((total_size_after + size_before))
                return
            fi
            ;;
        png)
            if ! optipng -quiet -o2 "$temp_file" 2>/dev/null; then
                echo -e "${RED}✗${NC} Compression error: $file"
                echo "$file - PNG compression failed" >> "$ERROR_LOG"
                error_count=$((error_count + 1))
                rm -f "$temp_file"
                total_size_after=$((total_size_after + size_before))
                return
            fi
            ;;
        gif)
            if ! gifsicle --batch --optimize=3 "$temp_file" 2>/dev/null; then
                echo -e "${RED}✗${NC} Compression error: $file"
                echo "$file - GIF compression failed" >> "$ERROR_LOG"
                error_count=$((error_count + 1))
                rm -f "$temp_file"
                total_size_after=$((total_size_after + size_before))
                return
            fi
            ;;
    esac
    
    # Check if compression achieved meaningful savings
    local size_after=$(get_file_size "$temp_file")
    local savings=$((size_before - size_after))
    local savings_percent=$((savings * 100 / size_before))
    
    if [ $savings_percent -ge $MIN_SAVINGS_PERCENT ] || [ "$needs_resize" = true ]; then
        mv "$temp_file" "$file"
        processed_images=$((processed_images + 1))
        total_size_after=$((total_size_after + size_after))
        
        local saved_formatted=$(format_bytes $savings)
        echo -e "${GREEN}✓${NC} Optimized: $filename (saved: $saved_formatted, ${savings_percent}%)"
    else
        rm -f "$temp_file"
        skipped_images=$((skipped_images + 1))
        total_size_after=$((total_size_after + size_before))
        echo -e "${BLUE}○${NC} Skipped: $filename (minimal savings: ${savings_percent}%)"
    fi
}

# Main execution
echo -e "${BLUE}Checking dependencies...${NC}"
check_dependencies
echo -e "${GREEN}✓ All dependencies found${NC}"
echo ""

echo -e "${BLUE}Starting optimization in: $(pwd)${NC}"
echo -e "${BLUE}Searching for images...${NC}"
echo ""

# Count images first to provide feedback
image_count=$(find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) | wc -l)

if [ "$image_count" -eq 0 ]; then
    echo -e "${YELLOW}No images found in current directory and subdirectories.${NC}"
    echo ""
    echo "Searched for: *.jpg, *.jpeg, *.png, *.gif (case-insensitive)"
    echo "Current directory: $(pwd)"
    echo ""
    echo "Please verify:"
    echo "  1. You're in the correct directory"
    echo "  2. Images exist in subdirectories"
    echo "  3. You have read permissions for the files"
    exit 0
fi

echo -e "${GREEN}Found $image_count images to process${NC}"
echo ""

# Create temporary file list
temp_list=$(mktemp)
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) > "$temp_list"

echo -e "${BLUE}Processing images...${NC}"
echo ""

# Process each image
line_count=0
while IFS= read -r file; do
    line_count=$((line_count + 1))
    if [ -n "$file" ]; then
        process_image "$file" || {
            echo -e "${RED}Failed to process: $file${NC}"
            echo "$file - Processing failed" >> "$ERROR_LOG"
        }
    fi
    # Show progress every 100 images
    if [ $((line_count % 100)) -eq 0 ]; then
        echo -e "${BLUE}Progress: $line_count images checked...${NC}"
    fi
done < "$temp_list"

echo ""
echo -e "${BLUE}Finished reading $line_count files from list${NC}"

if [ $line_count -eq 0 ]; then
    echo -e "${RED}Error: No files were read from temp list${NC}"
    cat "$temp_list"
fi

# Clean up temp file
rm -f "$temp_list"

# Calculate statistics
total_saved=$((total_size_before - total_size_after))
if [ $total_size_before -gt 0 ]; then
    total_saved_percent=$((total_saved * 100 / total_size_before))
else
    total_saved_percent=0
fi

# Print statistics
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OPTIMIZATION COMPLETE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Images Found:${NC}        $total_images"
echo -e "${GREEN}Images Processed:${NC}    $processed_images"
echo -e "${YELLOW}Images Resized:${NC}      $resized_images"
echo -e "${BLUE}Images Skipped:${NC}      $skipped_images"
echo -e "${RED}Errors:${NC}              $error_count"
echo ""
echo -e "${GREEN}Size Before:${NC}         $(format_bytes $total_size_before)"
echo -e "${GREEN}Size After:${NC}          $(format_bytes $total_size_after)"
echo -e "${GREEN}Total Saved:${NC}         $(format_bytes $total_saved) (${total_saved_percent}%)"
echo ""

if [ $error_count -gt 0 ]; then
    echo -e "${RED}Errors logged to: $ERROR_LOG${NC}"
    echo ""
fi

echo -e "${BLUE}========================================${NC}"