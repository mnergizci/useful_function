#!/usr/bin/env python3
'''
Created on 10/02/2024

@author: M. Nergizci, C. Magnard, M. Lazecky
University of Leeds
Gamma Remote Sensing
contact: mr.nergizci@gmail.com
'''
import numpy as np
import os
import py_gamma as pg
import sys
import subprocess
import shutil
import time
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.geometry import Point
from matplotlib.path import Path
from modules_sw_mn import * #functions saved here
import pickle
import LiCSAR_misc as misc



if len(sys.argv) < 1:
    print('Please provide pair information (assuming you run this in your BATCH_CACHE_DIR/frame)')
    print('e.g. python create_soi.py 20230129_20230210')
    print('Optional flag: -p for parallel processing, you need to run create_soi_00.py first!')
    sys.exit(1)

##variables
tempdir = os.getcwd()
frame = os.path.basename(tempdir)
framedir = tempdir
pair=sys.argv[1]
prime, second = pair.split('_')
tr= int(frame[:3])
metafile = os.path.join(os.environ['LiCSAR_public'], str(tr), frame, 'metadata', 'metadata.txt')
master = misc.grep1line('master=',metafile).split('=')[1]
master_slcdir = os.path.join(framedir, 'SLC', master)
GEOC_folder=os.path.join(framedir, 'GEOC')
RSLC_folder=os.path.join(framedir, 'RSLC')

if (not os.path.exists(os.path.join(RSLC_folder, prime))) or (not os.path.exists(os.path.join(RSLC_folder, second))):
    print('ERROR: some of the input epoch data does not exist in your RSLC folder')
    sys.exit(1)

#####variables for geocoding
lt_fine_suffix='lt_fine'
geo_dir= os.path.join(framedir, 'geo')
if os.path.exists(geo_dir) and os.path.isdir(geo_dir):
  for file in os.listdir(geo_dir):
    if file.endswith(lt_fine_suffix):
      lt_fine_file=os.path.join(geo_dir, file) 

  EQA_path=os.path.join(geo_dir, 'EQA.dem_par')
  EQA_par=pg.ParFile(EQA_path)
  widthgeo=EQA_par.get_value('width', dtype = int, index= 0)

else:
  print(f'geo folder doesnt exists. Please check your {framedir}')
#####

mli_par_path=os.path.join(RSLC_folder, master, master+ '.rslc.mli.par')
##the mli_par_path should be exist, othercase can't work properly!
try:
    if os.path.exists(mli_par_path):
        with open(mli_par_path, 'r') as mli_par:
            for line in mli_par:
                if line.startswith('range_samples'):
                    width = int(line.split(':')[-1].strip())
                elif line.startswith('azimuth_lines'):
                    az_line = int(line.split(':')[-1].strip())
    else:
        print(f'mli par does not exist. Please check the path: {mli_par_path}')
        sys.exit(1)

except Exception as e:
    print(f'An error occurred: {e}')
    sys.exit(1)


###scaling_calc
path_to_slcdir = os.path.join(framedir, 'RSLC', master)
sf_array=get_sf_array(path_to_slcdir, f0=5405000500, burst_interval=2.758277)
sf_array[sf_array==0]=np.nan
sf_array=sf_array*1000
scaling_factor_file = os.path.join(GEOC_folder,pair, f"{pair}.soi_scaling")
sf_array.astype(np.float32).byteswap().tofile(scaling_factor_file)


##geocoding
geoc_file=os.path.join(GEOC_folder,pair, f"{pair}.geo.soi_scaling")
exec_str=['geocode_back', scaling_factor_file, str(width), lt_fine_file, geoc_file, str(widthgeo), '0', '0', '0']
try:
  subprocess.run(exec_str, check=True, stdout=subprocess.DEVNULL)
  # print(f"Command executed successfully: {' '.join(exec_str)}")
except subprocess.CalledProcessError as e:
  print(f"An error occurred while executing the command: {e}")
    
geoc_tif=os.path.join(GEOC_folder,pair, f"{pair}.geo.soi_scaling.tif")
exec_str=['data2geotiff', EQA_path, geoc_file,'2', geoc_tif, '0.0']
try:
  subprocess.run(exec_str, check=True, stdout=subprocess.DEVNULL)
  # print(f"Command executed successfully: {' '.join(exec_str)}")
except subprocess.CalledProcessError as e:
  print(f"An error occurred while executing the command: {e}")


##removing
# Check if the file name contains '_soi_' and 'geo' and does not contain 'tif'
for i in os.listdir(os.path.join(GEOC_folder, pair)):
    if i.endswith('.soi_scaling'):
        os.remove(os.path.join(GEOC_folder, pair,i))  # Uncomment to remove the file
