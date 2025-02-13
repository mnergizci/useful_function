#!/bin/bash

# Set flag based on the argument provided
flag=0
if [ "$1" == "1" ]; then
  flag=1
fi

# Loop through each *.unw.tif or *.diff_pha.tif file
for i in 20*/20*.{unw,diff_pha}.tif; do
  if [ -f "$i" ] && [ $(stat -c%s "$i") -lt 10000000 ]; then
    # Print the directory name of the small file
    echo "$(basename "$(dirname "$i")")"

    # Check for associated .geo.diff* and .geo.unw* files in the same directory
    dir=$(dirname "$i")
    for extra in "$dir"/*.geo.diff* "$dir"/*.geo.unw*; do
      if [ -f "$extra" ]; then
        # Remove files if flag is set to 1
        if [ "$flag" -eq 1 ]; then
          rm "$extra"
          echo "Removed $extra"
        fi
      fi
    done
  fi
done