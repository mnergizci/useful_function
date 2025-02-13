#!/bin/bash
##change the permission for boi's.
#MN
# Loop through all the matching files
for file in */*adf*tif; do
    # Try to change the file permissions
    chmod 700 "$file"
    
    # Check if the chmod command was successful
    if [ $? -ne 0 ]; then
        # If chmod failed, print a warning message and continue to the next file
        echo "Warning: Permission denied for $file. Skipping..."
        continue
    fi
done

