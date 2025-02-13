#!/bin/bash

# Base directory
base_dir="/gws/nopw/j04/nceo_geohazards_vol1/public/LiCSAR_products/116/116A_04978_131311"

# Loop through each subdirectory in the base directory
for pair in "$base_dir"/*; do
    # Check if it is a directory and follows the naming pattern for pairs (e.g., numeric names or custom logic)
    if [ -d "$pair" ] && [[ $(basename "$pair") =~ ^[0-9]{8}$ ]]; then
        # Check if the specific file exists inside the directory
        if ! find "$pair" -maxdepth 1 -type f -name "*.geo.sbovldiff.adf.mm.tif" | grep -q .; then
            # If no matching file is found, print the pair name
            echo "Missing file in: $(basename "$pair")"
        fi
    fi
done
