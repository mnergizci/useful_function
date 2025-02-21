#!/usr/bin/env python3
'''
Created on 10/02/2024

@author: M Nergizci
University of Leeds,
contact:eemne@leeds.ac.uk
'''


import os
import re
import numpy
import subprocess
import os
import sys
import re
import time
import requests
import dateutil
import datetime as dt
import numpy as np
import warnings
import py_gamma as pg
from shapely.geometry import Polygon
from shapely.geometry import Point
#from matplotlib.colors import LinearSegmentedColormap as LSC
from matplotlib import pyplot as plt
from modules_sw_mn_testing import * 
#import matplotlib.path as path
import LiCSBAS_io_lib as io_lib
# import LiCSBAS_loop_lib as loop_lib
# import LiCSBAS_tools_lib as tools_lib
import pickle

if len(sys.argv) < 4:
    print('Please provide frame, pair and kernel size for median filtering of azimuth information: i.e python auto_cor_script.py 021D_05266_252525 20230129_20230210 96')
    sys.exit(1)

BLUE = '\033[94m'
ORANGE= '\033[38;5;208m'
RED = '\033[91m' 
GREEN = '\033[92m' 
ENDC = '\033[0m' 

# ANSI code to end formatting

##variables
frame=sys.argv[1]
pair=sys.argv[2]
kernel=np.int64(sys.argv[3])
batchdir=os.environ['BATCH_CACHE_DIR']
prime, second = pair.split('_')
framedir=os.path.join(batchdir, frame)
tr= int(frame[:3])

SLC_dir=os.path.join(framedir, 'SLC')
IFGdir=os.path.join(framedir, 'IFG')
RSLC_dir=os.path.join(framedir, 'RSLC')

###tiff example for exporting geotiff
GEOC_dir=os.path.join(framedir, 'GEOC')
geo_tif= os.path.join(GEOC_dir, pair, pair + '.geo.bovldiff.tif')
temp_file=os.path.join(framedir, 'temp_data')

a=os.listdir(SLC_dir)
for i in a:
    if i.startswith('2') and len(i) == 8:
        ref_epoc=i
mli_par=os.path.join(SLC_dir, ref_epoc, ref_epoc +'.slc.mli.par')
width=int(io_lib.get_param_par(mli_par, 'range_samples'))
length=int(io_lib.get_param_par(mli_par, 'azimuth_lines'))
print(width, length)
bovl=np.fromfile(os.path.join(IFGdir, pair, 'ddiff_pha_adf'), np.float32).reshape(length, width).byteswap()
bovl_coh=np.fromfile(os.path.join(IFGdir, pair, 'ddiff_coh_adf'), np.float32).reshape(length, width).byteswap()
if os.path.exists(os.path.join(IFGdir, pair, pair+'.azi')):
    azi=np.fromfile(os.path.join(IFGdir, pair, pair+'.azi'), np.float32).reshape(length, width).byteswap()
else:
    print(f"{os.path.join(pair+'.azi')} file doesnt exist pleas run the licsar_offset_tracking.py {pair}")
    sys.exit(1)
###I can make this function?? already in subswth_bovl_mn


# number of subswaths
nsubswaths = 3

# number of looks
rlks = 20
azlks = 4

# parameter file of the mosaic
SLC_par = pg.ParFile(os.path.join(RSLC_dir,prime, prime + '.rslc.par'))

# # TOPS parameter file of each subswath
TOPS_par = []
TOPS_par.append(pg.ParFile(os.path.join(RSLC_dir,prime,prime +'.IW1.rslc.TOPS_par')))
TOPS_par.append(pg.ParFile(os.path.join(RSLC_dir,prime,prime +'.IW2.rslc.TOPS_par')))
TOPS_par.append(pg.ParFile(os.path.join(RSLC_dir,prime,prime +'.IW3.rslc.TOPS_par')))

# # read SLC parameters
r0 = SLC_par.get_value('near_range_slc', index = 0, dtype = float)        # near range distance
rps = SLC_par.get_value('range_pixel_spacing', index = 0, dtype = float)  # range pixel spacing
t0 = SLC_par.get_value('start_time', index = 0, dtype = float)            # time of first azimuth line
tazi = SLC_par.get_value('azimuth_line_time', index = 0, dtype = float)   # time between each azimuth line


# get number of bursts per subswath
# max_nbursts = 0
# nbursts = []
# for sw in range(nsubswaths):
#   nbursts.append(TOPS_par[sw].get_value('number_of_bursts', index = 0, dtype = int))
#   if nbursts[sw] > max_nbursts:
#     max_nbursts = nbursts[sw]
max_nbursts = 0
min_nbursts = float('inf')  # Initialize min_nbursts to infinity
nbursts = []

# Find the max and min number of bursts
for sw in range(nsubswaths):
    nb = TOPS_par[sw].get_value('number_of_bursts', index=0, dtype=int)  # Mocked function call
    nbursts.append(nb)
    if nb > max_nbursts:
        max_nbursts = nb
    if nb < min_nbursts:
        min_nbursts = nb

# Update nbursts to minimum burst size across all subswaths
nbursts = [min_nbursts] * nsubswaths



# initialize first and last range and azimuth pixel of each burst (SLC mosaic)
rpix0 = np.zeros((nsubswaths, min_nbursts))
rpix2 = np.zeros((nsubswaths, min_nbursts))
azpix0 = np.zeros((nsubswaths, min_nbursts))
azpix2 = np.zeros((nsubswaths, min_nbursts))

for sw in range(nsubswaths):
  for b in range(nbursts[sw]):
    # read burst window (modified burst window as in previous e-mail)
    ext_burst_win = TOPS_par[sw].get_value('ext_burst_win_%d' %(b+1))
    burst_win = TOPS_par[sw].get_value('burst_win_%d' %(b+1))
    #calculate pixel coordinates of bursts in mosaicked image
    rpix0[sw, b] = round((float(burst_win[0]) - r0) / rps)
    rpix2[sw, b] = round((float(burst_win[1]) - r0) / rps)
    azpix0[sw, b] = round((float(burst_win[2]) - t0) / tazi)
    azpix2[sw, b] = round((float(burst_win[3]) - t0) / tazi)


# first and last range and azimuth pixel of each burst (MLI mosaic / interferogram geometry)
rpix_ml0 = rpix0 / rlks
rpix_ml2 = (rpix2 + 1) / rlks - 1
azpix_ml0 = azpix0 / azlks
azpix_ml2 = (azpix2 + 1) / azlks - 1


#############find the overlap polygons in the radar coordinates:
# calculate intersection of bursts (subswath intersection)

bursts = []
overlaps_sw = {}  # Use a dictionary to store overlaps for each sw

for sw in range(0, 3):
    p_inter_sw = []
    offset = 30  # to create overlaps between bursts
    overlaps = []  # This will store overlaps for the current subswath

    for b0 in range(nbursts[sw] - 1):  # Ensure there's a next burst to compare with by stopping one early
        # Calculate the corners for the current burst polygon
        rg_az1 = [
            [rpix_ml0[sw, b0], azpix_ml0[sw, b0] - offset],
            [rpix_ml2[sw, b0], azpix_ml0[sw, b0] - offset],
            [rpix_ml2[sw, b0], azpix_ml2[sw, b0] + offset],
            [rpix_ml0[sw, b0], azpix_ml2[sw, b0] + offset]
        ]
        p0 = Polygon(rg_az1)
        bursts.append(p0)
    
        # Calculate the corners for the next burst polygon
        rg_az2 = [
            [rpix_ml0[sw, b0 + 1], azpix_ml0[sw, b0 + 1] - offset],
            [rpix_ml2[sw, b0 + 1], azpix_ml0[sw, b0 + 1] - offset],
            [rpix_ml2[sw, b0 + 1], azpix_ml2[sw, b0 + 1] + offset],
            [rpix_ml0[sw, b0 + 1], azpix_ml2[sw, b0 + 1] + offset]
        ]
        p1 = Polygon(rg_az2)
    
        # Calculate the overlap between the current burst and the next one
        overlap = p0.intersection(p1)
        overlaps.append(overlap)  # Add the overlap to the list for the current subswath

    overlaps_sw[sw] = overlaps  # Store the overlaps for the current subswath in the dictionary

##get dfdc values

path_to_slcdir=os.path.join(RSLC_dir,prime)
sfbo, sff, sfb=get_dfDC(path_to_slcdir, f0=5405000500, burst_interval=2.758277, returnka=False, returnperswath=False, returnscalefactor=True)

####let's m2rad for azi:

print('median filtering starting')

###filtering_azi

azi96_path=os.path.join(IFGdir, pair, pair + f'_azi{kernel}')

if os.path.exists(azi96_path):
    print(f'{kernel} median filtered azi exists, so skip to filtering!')
    azi96=np.fromfile(azi96_path, np.float32).reshape(length, width).byteswap()
else:
    print(f'{kernel} median filter not exits, filtering continue. It can take time...')
    azi96=medianfilt_res(azi, ws=kernel)
    azi96.byteswap().tofile(azi96_path)

print('median_filter is done!')

###geocoding progress    
###variables for geocoding
lt_fine_suffix='lt_fine'
geo_dir= os.path.join(framedir, 'geo')
if os.path.exists(geo_dir) and os.path.isdir(geo_dir):
  for file in os.listdir(geo_dir):
    if file.endswith(lt_fine_suffix):
      lt_fine_file=os.path.join(geo_dir, file) 
        
  EQA_path=os.path.join(geo_dir, 'EQA.dem_par')
  widthgeo=int(io_lib.get_param_par(EQA_path, 'width'))
  print(f' widthgeo; {widthgeo}')
else:
  print(f'geo folder doesnt exists. Please check your {framedir}')
geoc_file=os.path.join(temp_file, pair+ f'azi{kernel}.geo')
exec_str=['geocode_back', azi96_path, str(width), lt_fine_file, geoc_file, str(widthgeo), '0', '0', '0' ]
try:
  subprocess.run(exec_str, check=True)
  print(f"Command executed successfully: {' '.join(exec_str)}")
except subprocess.CalledProcessError as e:
  print(f"An error occurred while executing the command: {e}")


geoc_tif=os.path.join(temp_file, pair + f'_azi{kernel}.geo.tif')
exec_str=['data2geotiff', EQA_path, geoc_file,'2', geoc_tif, '0.0' ]
try:
  subprocess.run(exec_str, check=True)
  print(f"Command executed successfully: {' '.join(exec_str)}")
except subprocess.CalledProcessError as e:
  print(f"An error occurred while executing the command: {e}")





def optimize_azi_scaling(azi, overlaps_sw, sfbo):
    azi_adjusted = np.full(azi.shape, np.nan, dtype=azi.dtype)  # Başlangıçta tüm değerleri NaN ile doldur
    
    for sw, polygons in overlaps_sw.items():
        for polygon in polygons:
            minx, miny, maxx, maxy = polygon.bounds  # Poligonun sınırlarını al
            
            # Sınırları matrisin boyutlarına sığacak şekilde ayarla
            min_row, max_row = int(max(miny, 0)), int(min(maxy, azi.shape[0] - 1))
            min_col, max_col = int(max(minx, 0)), int(min(maxx, azi.shape[1] - 1))
            
            for row in range(min_row, max_row + 1):
                for col in range(min_col, max_col + 1):
                    if polygon.contains(Point(col, row)):  # Nokta poligon içinde mi kontrol et
                        azi_adjusted[row, col] = azi[row, col] * sfbo[sw]  # sfbo ile çarp

    return azi_adjusted

azi_rd_file=(os.path.join(temp_file, pair + f'_azi{kernel}_rad'))
if not os.path.exists(azi_rd_file):
    print('Azimuth offset values changing meter to radian.')
    sfbo_m2r = [1/x for x in sfbo]
    azi_rd = optimize_azi_scaling(azi96, overlaps_sw, sfbo_m2r)
    # Assuming you have a function to save azi_rd to a file, which might look like this:
    azi_rd.astype(np.float32).byteswap().tofile(azi_rd_file)
else:
    print(f'{azi_rd_file} already exists.')
    # When loading, specify dtype and reshape
    azi_rd = np.fromfile(azi_rd_file, dtype=np.float32).reshape(length, width).byteswap()
####so we have azi bovl and sovl in radian base. We can make mathematical calculation easily rigth now.

print('meter2radian done! Wrapping calculating is just started!')
##coh masking
###coherence thresholding 0.7
threshold=0.4
mask_cc=(bovl_coh >threshold).astype(int)

###to get rid of edge problem
bovl_nan = np.where(bovl == 0, np.nan, bovl)
masknp = ~np.isnan(bovl_nan)
mask_cc=mask_cc*masknp
######


bovlrad_cc=bovl*mask_cc
azi_rd_cc=azi_rd*mask_cc
azi_rd_cc[azi_rd_cc==0]=np.nan

diff=bovlrad_cc-azi_rd_cc
diff=np.nan_to_num(diff)
diff_wrap= np.mod(diff + np.pi, 2*np.pi) - np.pi
azbovlrad=azi_rd_cc+diff_wrap
# azbovlrad[azbovlrad==0]=np.nan
azbovlrad_file=os.path.join(temp_file, pair + f'_azibovl{kernel}_rad')
azbovlrad = azbovlrad.astype(np.float32)
azbovlrad.byteswap().tofile(azbovlrad_file)  # Corrected method chain for saving

print('Unwrapped bovl values changing rad2m')

azbovlmeter_file = os.path.join(temp_file, pair + f'_azibovl{kernel}_meter')
if not os.path.exists(azbovlmeter_file):
    azbovlmeter_temp = optimize_azi_scaling(azbovlrad, overlaps_sw, sfbo)
    print('rad2m is done!')
    azbovlmeter = np.nan_to_num(azbovlmeter_temp, nan=0)
    azbovlmeter = azbovlmeter.astype(np.float32)
    azbovlmeter.byteswap().tofile(azbovlmeter_file)  # Corrected method chain for saving
else:
    print(f'{azbovlmeter_file} already exists')
    azbovlmeter = np.fromfile(azbovlmeter_file, dtype=np.float32).reshape(length, width).byteswap()

# print('printing')
# plt.figure(figsize=(20, 20))
# plt.imshow(azbovlmeter, cmap='bwr')
# plt.colorbar()
# plt.savefig('azbovlmeter.png')

# print('printing')
# plt.figure(figsize=(20, 20))
# plt.imshow(azbovlrad, cmap='bwr', vmin=-10, vmax=10)
# plt.colorbar()
# plt.savefig('azbovlrad.png')

###save geotiff.
#output_bovl=os.path.join(GEOC_dir, pair, pair, + '.geo.bovl_unw.tif')


print('Geocoding starting')

###variables for geocoding
lt_fine_suffix='lt_fine'
geo_dir= os.path.join(framedir, 'geo')
if os.path.exists(geo_dir) and os.path.isdir(geo_dir):
  for file in os.listdir(geo_dir):
    if file.endswith(lt_fine_suffix):
      lt_fine_file=os.path.join(geo_dir, file) 
        
  EQA_path=os.path.join(geo_dir, 'EQA.dem_par')
  widthgeo=int(io_lib.get_param_par(EQA_path, 'width'))
  print(f' widthgeo; {widthgeo}')
else:
  print(f'geo folder doesnt exists. Please check your {framedir}')


###geocoding progress
geoc_file=os.path.join(temp_file, pair + f'_azibovl{kernel}_meter.geo')
exec_str=['geocode_back', azbovlmeter_file, str(width), lt_fine_file, geoc_file, str(widthgeo), '0', '0', '0' ]
try:
  subprocess.run(exec_str, check=True)
  print(f"Command executed successfully: {' '.join(exec_str)}")
except subprocess.CalledProcessError as e:
  print(f"An error occurred while executing the command: {e}")
    
geoc_tif=os.path.join(temp_file,pair + f'_azibovl{kernel}_meter.geo.tif')
exec_str=['data2geotiff', EQA_path, geoc_file,'2', geoc_tif, '0.0' ]
try:
  subprocess.run(exec_str, check=True)
  print(f"Command executed successfully: {' '.join(exec_str)}")
except subprocess.CalledProcessError as e:
  print(f"An error occurred while executing the command: {e}")
#################################
#################################


print(BLUE + 'unwrapped BOI is done! Lets go for SOI!' + ENDC)

####I need to change for 0.6 in subswath_bovl_mn.

sovl=np.fromfile(os.path.join(temp_file, pair + '_merged_soi_phase_m'), np.float32).reshape(length, width).byteswap()
sovl_coh=np.fromfile(os.path.join(temp_file, pair + '_diff_double_mask_coh'), np.float32).reshape(length, width).byteswap()

bwrs=os.path.join(temp_file,frame +'_bwr.pkl')
fwrs=os.path.join(temp_file,frame +'_fwr.pkl')

if not os.path.exists(bwrs) and not os.path.exists(fwrs):
    print(RED + 'The bwr and fwr polygons not in the folder. Please run: subswath_bovl_mn.py in the $batchdir' + ENDC)

else:
    with open(bwrs, 'rb') as f:
        bwr = pickle.load(f)
    
    with open(fwrs, 'rb') as f:
        fwr = pickle.load(f)



####
####masking for dataset.
######
threshold=0.6
mask_cc=(sovl_coh >threshold).astype(int)
###to get rid of edge problem
sovl_nan = np.where(sovl == 0, np.nan, sovl)
masknp = ~np.isnan(sovl_nan)
mask_cc=mask_cc*masknp

#### Scaling factor
sf_array=get_sf_array(path_to_slcdir, f0=5405000500, burst_interval=2.758277)
sf_array[sf_array==0]=np.nan
sf_array_cc=mask_cc*sf_array
azi96_rad=azi96/sf_array
azi96_rad_cc=mask_cc*azi96_rad
sovl_rad=sovl/sf_array
sovl_rad_cc=mask_cc*sovl_rad

diff=sovl_rad_cc-azi96_rad_cc
diff_nonan=np.nan_to_num(diff)
diff_wrap=np.mod(diff_nonan+ np.pi, 2*np.pi) - np.pi
diff_unw_rad=azi96_rad_cc+diff_wrap
diff_unw_m=diff_unw_rad*sf_array_cc

print('Unwrapping step is done!')

aziSOImeter=diff_unw_m.astype(np.float32)
aziSOImeter_file=os.path.join(temp_file, pair +'_aziSOImeter')
aziSOImeter.byteswap().tofile(aziSOImeter_file)



###geocoding progress
geoc_file=os.path.join(temp_file, pair +'_aziSOI_meter.geo')
exec_str=['geocode_back', aziSOImeter_file, str(width), lt_fine_file, geoc_file, str(widthgeo), '0', '0', '0' ]
try:
  subprocess.run(exec_str, check=True)
  print(f"Command executed successfully: {' '.join(exec_str)}")
except subprocess.CalledProcessError as e:
  print(f"An error occurred while executing the command: {e}")
    
geoc_tif=os.path.join(temp_file, pair + '_aziSOI_meter.geo.tif')
exec_str=['data2geotiff', EQA_path, geoc_file,'2', geoc_tif, '0.0' ]
try:
  subprocess.run(exec_str, check=True)
  print(f"Command executed successfully: {' '.join(exec_str)}")
except subprocess.CalledProcessError as e:
  print(f"An error occurred while executing the command: {e}")
#################################
#################################



    


