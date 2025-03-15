#!/bin/bash

# Ensure extension is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <extension>"
  echo "Example: $0 unw OR $0 diff_pha"
  exit 1
fi

ext=$1  # Set extension from user input

# Loop through numeric directories [0-9]*
for dir in [0-9]*; do 
  if [ -d "$dir" ]; then
    echo "Processing directory: $dir"

    # Loop through GEOC/202* inside each directory
    for geoc_dir in "$dir"/GEOC/202*; do
      if [ -d "$geoc_dir" ]; then
        echo "Applying GACOS_SET_Iono correction in $(basename "$geoc_dir") with extension $ext"
        (cd "$dir" && correction_gacos_set_iono.sh "$(basename "$PWD")" "$(basename "$geoc_dir")" "$ext")
      else
        echo "Skipping $geoc_dir (not a directory)"
      fi
    done
  else
    echo "Skipping $dir (not a directory)"
  fi
done
