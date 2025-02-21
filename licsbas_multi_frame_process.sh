#!/bin/bash
##Muhammet Nergizci, COMET, University of Leeds-2025
# Function to display usage
usage() {
    echo "Usage: $0 <frames_file> [-s start_date] [-e end_date] [--local] [--sbovl] [--eqoff]"
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
local_flag=""

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
        --local)
            local_flag="--local"
            shift
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

    tmux_command=""
    if [[ -n "$local_flag" ]]; then
        tmux_command="licsbas_local; "
    fi

    if [[ "$sboi_flag" == "--sbovl" && -n "$eqoff_flag" ]]; then
        tmux_command+="licsar2licsbas_testing.sh -W -M 10 -b -n 4 -T -E 6 '$i' '$start_date' '$end_date'"
    elif [[ "$sboi_flag" == "--sbovl" ]]; then
        tmux_command+="licsar2licsbas_testing.sh -W -M 10 -b -n 4 -T '$i' '$start_date' '$end_date'"
    elif [[ -n "$eqoff_flag" ]]; then
        tmux_command+="licsar2licsbas.sh -M 10 -g -n 4 -W -N -T -i -e -u -t 0 -C 0.2 -d -E 6 -p '$i' '$start_date' '$end_date'"
    else
        tmux_command+="licsar2licsbas.sh -M 10 -g -n 4 -W -N -T -i -e -u -t 0 -C 0.2 -d -p '$i' '$start_date' '$end_date'"
    fi

    tmux_command+=" >> '${log_dir}/${i}_out.log' 2>> '${log_dir}/${i}_err.log' && echo 'Job for $i completed; bash'"
    # echo "Command: $tmux_command"
    tmux new-session -d -s "$session_name" "$tmux_command"

done < "$frames_file"