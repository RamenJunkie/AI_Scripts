#!/bin/sh

# A Shell script that will merge folders together into a merged file, creating versions of any conflicts.  Used to merge downloads from Archive.org Scrapes which come out ugly, but useful for other things probably.
set -eu

# Usage check
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <basefolder>"
    exit 1
fi

BASE="$1"
DEST="$BASE/merged"

# Ensure basefolder exists
if [ ! -d "$BASE" ]; then
    echo "Error: Base folder '$BASE' not found."
    exit 1
fi

mkdir -p "$DEST"

echo "Merging folders inside: $BASE"
echo "Destination: $DEST"
echo

# Loop through all subfolders (excluding merged itself)
for SRC in "$BASE"/*/; do
    [ "$SRC" = "$DEST/" ] && continue
    echo "→ Merging from: $SRC"

    # Find all files recursively
    find "$SRC" -type f | while IFS= read -r FILE; do
        REL_PATH="${FILE#$SRC}"
        DEST_PATH="$DEST/$REL_PATH"
        DEST_DIR=$(dirname "$DEST_PATH")

        mkdir -p "$DEST_DIR"

        if [ ! -e "$DEST_PATH" ]; then
            cp -p "$FILE" "$DEST_PATH"
        else
            # Add version suffix if file exists
            NAME="${DEST_PATH%.*}"
            EXT="${DEST_PATH##*.}"

            # Handle files without an extension
            if [ "$NAME" = "$DEST_PATH" ]; then
                EXT=""
            else
                EXT=".$EXT"
            fi

            i=2
            while [ -e "${NAME}_v${i}${EXT}" ]; do
                i=$((i + 1))
            done

            NEW_PATH="${NAME}_v${i}${EXT}"
            cp -p "$FILE" "$NEW_PATH"
            echo "   Duplicate: $(basename "$REL_PATH") → $(basename "$NEW_PATH")"
        fi
    done
done

echo
echo "✅ Merge complete."
echo "Merged content available in: $DEST"
