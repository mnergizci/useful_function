#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 <frames_file>"
    exit 1
}

# Check if at least one argument is provided
if [ $# -lt 1 ]; then
    usage
fi

# Default values
frames_file=""

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -*)
            echo "Unknown option: $1"
            usage
            ;;
        *)
            frames_file="$1"
            shift
            ;;
    esac
done

# Validate mandatory argument
if [[ -z "$frames_file" ]]; then
    usage
fi

# Extract the desired part of the current directory path
current_dir_suffix=$(pwd | awk -F'/' '{print $(NF-1)"/"$NF}')

# Process each frame in the input file
while read -r i; do
    # Validate frame format
    if ! [[ "$i" =~ ^[0-9]{3}[AD]_[0-9]{5}_[0-9]{6}$ ]]; then
        echo "Skipping invalid frame: $i"
        continue
    fi

    session_name="${i}_${current_dir_suffix}_gapfill"
    echo "Starting session: $session_name"

    # Check if directory exists before executing
    if [ -d "$i" ]; then
        tmux new-session -d -s "$session_name" "cd '$i' && framebatch_gapfill.sh -b -o 2"
    else
        echo "Skipping $i: Directory does not exist."
    fi

done < "$frames_file"
