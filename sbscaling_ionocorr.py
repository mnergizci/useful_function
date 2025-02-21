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
from scipy.constants import speed_of_light


if len(sys.argv) < 1:
    print('Please provide pair information (assuming you run this in your BATCH_CACHE_DIR/frame)')
    print('e.g. python sbscaling_ionocorr.py 20230129_20230210')
    print('Optional flag: -p for parallel processing, you need to run create_soi_00.py first!')
    sys.exit(1)

##variables
tempdir = os.getcwd()
frame = os.path.basename(tempdir)
batchdir = os.environ['BATCH_CACHE_DIR'] #this is necesarry because the framebatch_gapfill run the code in $LiCS_temp folder which not correct location.
framedir = os.path.join(batchdir, frame)
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

azpix=14000
PRF = 486.486
k = 40.308193 # m^3 / s^2
f0 = 5.4050005e9
c = speed_of_light
#fH = f0 + dfDC*0.5
#fL = f0 - dfDC*0.5

scaling_tif=os.path.join(GEOC_folder, pair, pair +'.geo.sbovl_scaling.tif')
outtif=os.path.join(GEOC_folder, pair, pair +'.geo.sbovl_ionocorr_mm.tif')
scaling_factor=load_tif2xr(scaling_tif)
dfDC=azpix*PRF/(2*np.pi*scaling_factor)

###
fH = f0 + dfDC*0.5
fL = f0 - dfDC*0.5
###

 ##This will be seperate in the future #TODO
TEC_sA_t0_tif=TEC_sB_t0_tif=os.path.join(os.environ['LiCSAR_public'], str(tr), frame,'epochs',prime, prime+'.geo.iono.code.sTEC.tif')
TEC_sA_t1_tif=TEC_sB_t1_tif=os.path.join(os.environ['LiCSAR_public'], str(tr), frame,'epochs',second, second+'.geo.iono.code.sTEC.tif')

###
TEC_sA_t0=load_tif2xr(TEC_sA_t0_tif)
TEC_sA_t1=load_tif2xr(TEC_sA_t1_tif)
delta_TEC_sB = delta_TEC_sA = TEC_sA_t1-TEC_sA_t0
###
# phaionL = -4*np.pi*k/c/fL * selected_frame_esds['TECS_B']  # - TEC_master_B1)
# phaionH = -4*np.pi*k/c/fH * selected_frame_esds['TECS_A']  # - TEC_master_B2)
Uaziono_mm=(2*PRF*k)/(c*dfDC) *(delta_TEC_sA/fH-delta_TEC_sB/fL)*14000
export_xr2tif(Uaziono_mm, outtif)  