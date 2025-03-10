#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 <frames_file> [-s start_date] [-e end_date] [-b]"
    exit 1
}

# Check if at least one argument is provided
if [ $# -lt 1 ]; then
    usage
fi

# Default values
frames_file=""
start_date=""
end_date=""
batch2selection=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--start-date)
            start_date="$2"
            shift 2
            ;;
        -e|--end-date)
            end_date="$2"
            shift 2
            ;;
        -b|--batch)
            batch_mode=true
            shift
            ;;
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

# Validate mandatory arguments
if [ -z "$frames_file" ] || [ -z "$start_date" ] || [ -z "$end_date" ]; then
    usage
fi

# Convert YYYYMMDD to YYYY-MM-DD
start_date="${start_date:0:4}-${start_date:4:2}-${start_date:6:2}"
end_date="${end_date:0:4}-${end_date:4:2}-${end_date:6:2}"

# Change to batch directory if it exists
if [ "$batch_mode" = true ]; then
    batch2
fi

if [ -n "$BATCH_CACHE_DIR" ] && [ -d "$BATCH_CACHE_DIR" ]; then
    cd "$BATCH_CACHE_DIR" || exit 1
fi

##Create nla_requests_log directory if doesn't exist
# Create nla_requests_log directory inside BATCH_CACHE_DIR if it doesn't exist
log_dir="${BATCH_CACHE_DIR}/nla_requests_log"
mkdir -p "$log_dir"

# Extract the desired part of the current directory path
current_dir_suffix=$(pwd | awk -F'/' '{print $(NF-1)"/"$NF}')

# Process each frame in the input file
while read -r i; do
    # Validate frame format
    if ! [[ "$i" =~ ^[0-9]{3}[AD]_[0-9]{5}_[0-9]{6}$ ]]; then
        echo "Skipping invalid frame: $i"
        continue
    fi
    session_name="${i}_${current_dir_suffix}"
    echo $session_name

    # Determine command based on batch mode flag
    if [ "$batch_mode" = true ]; then
        run_command="batch2; LiCSAR_0_getFiles.py -f '$i' -s '$start_date' -e '$end_date' -r -b Y -n "		

    else
        run_command="batch3; LiCSAR_0_getFiles.py -f '$i' -s '$start_date' -e '$end_date' -r -b Y -n"
    fi

    tmux new-session -d -s "$session_name" \
    "$run_command >> '${log_dir}/${i}_nla_req_out.log' 2>> '${log_dir}/${i}_nla_req_err.log' && echo 'Job for $i completed; bash'"
done < "$frames_file"
