#!/usr/bin/env python3
'''
Last Revision August 2024

@author: M. Nergizci
University of Leeds,
contact: mr.nergizci@gmail.com
'''
import numpy as np
import os
import sys
import subprocess
import shutil
from modules_sw_mn import * #functions saved here


if len(sys.argv) < 2:
    print('Please provide pair information: i.e python sbscaling_tif.py 20230129_20230210')
    sys.exit(1)

# User feedback with ANSI colors
BLUE = '\033[94m'
ORANGE = '\033[38;5;208m'
ENDC = '\033[0m'  # ANSI code to end formatting

##variables
tempdir = os.getcwd()
frame = os.path.basename(tempdir)
batchdir = os.environ['BATCH_CACHE_DIR'] ##this is necesarry because the framebatch_gapfill run the code in $LiCS_temp folder which not correct location.
framedir = os.path.join(batchdir, frame)
#TODO I can check the frame name is okay for format of LiCSAR_frame.
pair = sys.argv[1]
#batchdir = os.environ['BATCH_CACHE_DIR']
prime, second = pair.split('_')
#framedir = os.path.join(batchdir, frame)
IFG_folder = os.path.join(framedir, 'IFG')
GEOC_folder = os.path.join(framedir, 'GEOC')

# Define the paths
boi_path = os.path.join(GEOC_folder, pair, pair + '.geo.boi_scaling.tif')
soi_path = os.path.join(GEOC_folder, pair, pair + '.geo.soi_scaling.tif')
output_path = os.path.join(GEOC_folder, pair, pair + '.geo.sbovl_scaling.tif')


# Open input GeoTIFF files
if os.path.exists(boi_path):
    boi_mm = open_geotiff(boi_path, fill_value=np.nan)
else:
    print(f"{boi_path} doesn't exist ,please run bscaling_tif.py first!")
    sys.exit(1)
    
if os.path.exists(soi_path):
    soi = open_geotiff(soi_path, fill_value=np.nan)
else:
    print(f"{soi_path} doesn't exist ,please run sscaling_tif.py first!")
    sys.exit(1)


# Process the data
super_sboi = boi_mm.copy()
super_sboi[super_sboi==0]= np.nan
soi[soi==0]= np.nan
super_sboi[np.isnan(super_sboi)] = soi[np.isnan(super_sboi)]

# Export the result to a GeoTIFF
export_to_tiff(output_path, super_sboi, boi_path)