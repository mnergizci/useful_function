#!/bin/bash
# Usage: correction_gacos_set_iono.sh frame_id ifg ext
# Example: correction_gacos_set_iono.sh 012A_06041_131313 20250105_20250117 diff_pha

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
  echo "Usage: correction_gacos_set_iono.sh frame_id ifg ext"
  echo "(ifg must be yyyymmdd_yyyymmdd)"
  echo "(ext should be either diff_pha, diff_unfiltered_pha, or unw)"
  exit 1
fi

frame=$1
ifg=$2
ext=$3

if [[ "$frame" != *"_"* ]]; then
  echo "Warning: This is not a standard frame ID. Check your input parameters."
fi

track=$(echo "$frame" | cut -c -3 | sed 's/^0*//')

# Define paths
indir="$LiCSAR_public/$track/$frame/interferograms"
epochdir="$LiCSAR_public/$track/$frame/epochs"
ifgpath="$indir/$ifg"
infile="$ifgpath/$ifg.geo.$ext.tif"

date1=$(echo "$ifg" | cut -d '_' -f1)
date2=$(echo "$ifg" | cut -d '_' -f2)

# Define correction files
gacos1="$epochdir/$date1/${date1}.sltd.geo.tif"
gacos2="$epochdir/$date2/${date2}.sltd.geo.tif"
set1="$epochdir/$date1/${date1}.tide.geo.tif"
set2="$epochdir/$date2/${date2}.tide.geo.tif"
ion1="$epochdir/$date1/${date1}.geo.iono.code.tif"
ion2="$epochdir/$date2/${date2}.geo.iono.code.tif"

# Check if epochs directory exists
if [ ! -d "$epochdir" ]; then
  echo "Warning: Epochs directory does not exist for this frame: $epochdir"
fi

# Check if interferogram exists
if [ ! -f "$infile" ]; then
  echo "Error: Interferogram file does not exist: $infile"
  exit 1
fi

# Check and request missing correction files
for corr_file in "$gacos1" "$gacos2"; do  #"$set1" "$set2" "$ion1" "$ion2"
  if [ ! -f "$corr_file" ]; then
    echo "Correction file missing: $corr_file"
    echo "Attempting to request missing data..."
    framebatch_update_gacos.sh "$frame"

    # Re-check after request
    if [ ! -f "$corr_file" ]; then
      echo "Error: Correction file still missing after request: $corr_file"
      exit 1
    fi
  fi
done

# Ensure required tools are installed
if ! command -v gmt &> /dev/null; then
  echo "Error: GMT is not installed. Please install GMT before running this script."
  exit 1
fi

# if ! command -v ifg_remove_gacostideiono_correction.py &> /dev/null; then
#   echo "Error: Python script ifg_remove_gacostideiono_correction.py not found. Check your installation."
#   exit 1
# fi

# Define output file
outfile="$ifgpath/$ifg.geo.$ext.gacos_set_iono.tif"

echo "Applying GACOS, SET, and Ionospheric corrections to $ifg"
echo "Corrected file will be saved to: $outfile"

# Run the correction script
ifg_remove_gacostideiono_correction.py "$infile" "$gacos1" "$gacos2" "$set1" "$set2" "$ion1" "$ion2" "$ext" "$outfile"

# Generate a preview of the corrected interferogram
if [ "$ext" == "unw" ]; then
  create_preview_unwrapped "$outfile"
else
  create_preview_wrapped "$outfile"
fi

echo "Correction completed successfully for $ifg"
exit 0
