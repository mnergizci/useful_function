#!/bin/bash

# Check if both a frameid/folder and a suffix were provided
if [ $# -ne 2 ]; then
  echo "Usage: $0 <frameid/folder> <suffix>"
  echo "Example: $0 021D_05266_252525/GEOC cc.png"
  exit 1
fi

frameid=$1  # The frameid/folder provided as the first argument
suffix=$2   # The suffix provided as the second argument

# Loop through all directories under the specified frameid/folder
for dir in $BATCH_CACHE_DIR/$frameid/*/ ; do
    # Check if the directory does not contain any files matching the provided suffix
    if [ -z "$(find ${dir} -maxdepth 1 -type f -name "*.${suffix}" 2>/dev/null)" ]; then
        # Print the directory name, removing the prefix and trailing slash for readability
        echo "${dir#${BATCH_CACHE_DIR}/%}"
    fi
done

