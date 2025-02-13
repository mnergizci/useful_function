#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 <frames_file> [-s start_date] [-e end_date] [--sbovl] [--eqoff]"
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
sboi_flag=""
eqoff_flag=""

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
        --sbovl)
            sboi_flag="--sbovl"
            shift
            ;;
        --eqoff)
            eqoff_flag="--eqoff"
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
if [[ -z "$frames_file" || -z "$start_date" || -z "$end_date" ]]; then
    usage
fi

# Create the LiCSBAS_log directory for multi-frame processing logs
log_dir="LiCSBAS_log"
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
    echo "Starting session: $session_name"

    if [[ "$sboi_flag" == "--sbovl" && -n "$eqoff_flag" ]]; then
        # Run with SBOI and eqoff options
        tmux new-session -d -s "$session_name" \
        "licsbas_local; licsar2licsbas_testing.sh -W -M 10 -b -n 4 -T -E 6 '$i' '$start_date' '$end_date' >> '${log_dir}/${i}_out.log' 2>> '${log_dir}/${i}_err.log' && echo 'Job for $i completed; bash'"
    
    elif [[ "$sboi_flag" == "--sbovl" ]]; then
        # Run with only SBOI option
        tmux new-session -d -s "$session_name" \
        "licsbas_local; licsar2licsbas_testing.sh -W -M 10 -b -n 4 -T '$i' '$start_date' '$end_date' >> '${log_dir}/${i}_out.log' 2>> '${log_dir}/${i}_err.log' && echo 'Job for $i completed; bash'"
    
    elif [[ -n "$eqoff_flag" ]]; then
        # Run with only eqoff option
        tmux new-session -d -s "$session_name" \
        "licsbas_local; licsar2licsbas_testing.sh -M 10 -g -n 4 -W -T -i -e -u -t 0 -C 0.2 -d -E 6 -p '$i' '$start_date' '$end_date' >> '${log_dir}/${i}_out.log' 2>> '${log_dir}/${i}_err.log' && echo 'Job for $i completed; bash'"
    
    elif [[ -z "$sboi_flag" && -z "$eqoff_flag" ]]; then
        # Run without SBOI or eqoff
        tmux new-session -d -s "$session_name" \
        "licsbas_local; licsar2licsbas_testing.sh -M 10 -g -n 4 -W -T -i -e -u -t 0 -C 0.2 -d -p '$i' '$start_date' '$end_date' >> '${log_dir}/${i}_out.log' 2>> '${log_dir}/${i}_err.log' && echo 'Job for $i completed; bash'"
    fi

done < "$frames_file"
