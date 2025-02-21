#!/bin/bash

# 2024 MN

#Check if both arguments are provided
if [ -z "$2" ]; then
    echo "USAGE: please provide the frame ID and the IFG list which includes pairs you'd like to generate BOI for."
    echo "Example: boi_auto.sh frame_id boi_list.txt"
    exit 1
fi

frame=$1
list=$2

# Loop through each line in the provided list file
for i in $(cat "$list"); do
    boi_name="$BATCH_CACHE_DIR/$frame/GEOC/$i/$i.geo.bovldiff.adf.mm.tif"

    # Check if the file already exists
    if [ -f "$boi_name" ]; then
        echo "The BOI already exists for $i, so we will skip this one."
        continue  # Skip the rest of the loop for this iteration
    fi

    # If the file does not exist, echo the item (placeholder for further processing)
    echo "Processing item: $i"
    create_bovl_ifg.sh $i 1
done
