#!/usr/bin/env python3
from lics_unwrap import *
import framecare as fc
from scipy import ndimage 
from geocube.api.core import make_geocube
import geopandas as gpd
import daz_lib_licsar as dl
import LiCSAR_misc as misc
import sys
import rasterio
from rasterio.merge import merge
import os
import numpy as np

'''
This code helps to scale factor bovl and save the metadata file, as a part of ionospheric correction in licsar2licsbas
Nergizci 05/11/2024
'''

# Get the current working directory (assumed to be GEOC)
GEOCdir = os.getcwd()
framedir = os.path.dirname(GEOCdir)
frame = os.path.basename(framedir)

# Standard frame name pattern in LiCS (e.g., 116A_05207_252525)
frame_pattern = r"^\d{3}[AD]_\d{5}_\d{6}$"
# print(f"Checking directories:\n - GEOCdir: {GEOCdir}\n - framedir: {framedir}\n - frame: {frame}")

if not re.match(frame_pattern, frame):
    print("Please check where you are running the script. It should be in the GEOC folder with a correctly formatted frame name.")
    sys.exit(1)

# Define metadata file path
tr = int(frame[:3])
metadir = os.path.join(os.environ['LiCSAR_public'], str(tr), frame, 'metadata')
metafile = os.path.join(metadir, 'metadata.txt')

# Extract primary epoch from metadata
try:
    primepoch = misc.grep1line('master=', metafile).split('=')[1]
    path_to_slcdir = os.path.join(os.environ['LiCSAR_procdir'], str(tr), frame, 'SLC', primepoch)
except Exception as e:
    print(f"Error reading metadata file: {e}")
    sys.exit(1)

# Find a valid pair with the required file
pair = None
for pairs in os.listdir(GEOCdir):
    pair_dir = os.path.join(GEOCdir, pairs)
    if os.path.isdir(pair_dir):
        bovl_tif = os.path.join(pair_dir, f"{pairs}.geo.bovldiff.adf.mm.tif")
        if os.path.exists(bovl_tif) and os.path.getsize(bovl_tif) > 0:
            pair = pairs
            print(f"Found matching pair: {pair}")
            break

# Check if a valid pair was found
if pair is None:
    print("No valid interferogram pair found containing 'geo.bovldiff.adf.mm.tif'.")
    sys.exit(1)

# Define input and output TIFF files
tif = os.path.join(GEOCdir, pair, f"{pair}.geo.bovldiff.adf.tif")
outtif = os.path.join(GEOCdir, f"{pair}.geo.bovl_scaling.tif")

###Lazecky conncomps idea
bovlpha=load_tif2xr(tif)
bovlpha = bovlpha.where(bovlpha!=0) # to get rid of zero --now will be nan
aa = bovlpha.copy()
npa = aa.values
npa[npa==0] = np.nan
mask = ~np.isnan(npa)
conncomps, ncomp = ndimage.label(mask) 
aa.values = conncomps
conncomps = aa #just for clarity
conncomps = conncomps.where(~np.isnan(bovlpha))

#geopandas dataframe of burst overlap from functions lib.
##bursts geojson
bovljson = os.path.join(fc.get_frame_path(frame, 'procdir'), frame+'.bovls.geojson')
if not os.path.exists(bovljson):
    print('extracting burst polygons from LiCSInfo database')
    gpd_bursts = fc.frame2geopandas(frame, use_s1burst=True)
    try:
        gpd_bursts.to_file(bovljson, driver='GeoJSON')
    except:
        print('cannot write to LiCSAR_proc, saving locally')
        bovljson = frame+'.bovls.geojson'
        gpd_bursts.to_file(bovljson, driver='GeoJSON')
#gpd_overlaps, overlap_gdf1, overlap_gdf2, overlap_gdf3 = extract_burst_overlaps(frame)
gpd_overlaps, sw_overlaps_dict = fc.extract_burst_overlaps(frame, os.path.dirname(os.path.realpath(bovljson)))

#calculate dfDC from daz_library
PRF=486.486
az_res=14000 ##it can be improved extracting from par file 
dfDCs=dl.get_dfDC(path_to_slcdir, f0=5405000500, burst_interval=2.758277, returnka=False, returnperswath=True) # no bursts in swath = np.nan (i.e. dfDCs will always have 3 values, corresp. to swaths)

##rad2mm scaling factor.
scaling_factors = dict()
for sw in sw_overlaps_dict.keys():
    scaling_factors[sw] = (az_res*PRF) / (dfDCs[sw-1]* 2 * np.pi)

tif_list = []
outbovl = bovlpha*0

####
bovlpha = bovlpha.where((bovlpha != 0) & ~np.isnan(bovlpha), np.nan)
bovlpha = bovlpha.where(np.isnan(bovlpha), 1)
####

for subswath in sw_overlaps_dict.keys():
    # Create a GeoDataFrame for the current subswath
    crs = {"init": "epsg:4326"}
    sw_overlaps_dict[subswath] = sw_overlaps_dict[subswath].set_crs(crs, allow_override=True)
    g = gpd.GeoDataFrame(
        {'bovl': sw_overlaps_dict[subswath].index.values},
        geometry=sw_overlaps_dict[subswath].geometry,
        crs={"init": "epsg:4326"}
    )
    # Create a GeoCube with the same spatial dimensions as 'aa'
    bovls = make_geocube(vector_data=g, like=aa.rio.set_spatial_dims(x_dim='lon', y_dim='lat'))
    bovls = bovls.rename({'x': 'lon', 'y': 'lat'})

    # Interpolate the 'bovls' data to match the spatial dimensions of 'bovlpha'
    #bovls = bovls.rio.interp_like(bovlpha)
    bovls = bovls.interp_like(bovlpha)

    # Create a binary mask where 'bovls' is multiplied by 0 and then added by 1
    bovls = bovls * 0 + 1

    # Multiply 'bovlpha' by the binary mask 'bovls' to apply the mask
    bovlphatemp = bovlpha * bovls.bovl * scaling_factors[subswath]
    #if subswath in scaling_factors: # the concept should be actually opposite - but ok for now, good to test in some frame without one of subswaths
    #    bovlphatemp = bovlphatemp * scaling_factors[subswath]

    # add the grid values to the final output
    outbovl = outbovl.fillna(0) + bovlphatemp.fillna(0)


# much more elegant:
export_xr2tif(outbovl.where(outbovl != 0), outtif)      #.bovl, f'subswath{subswath}.tif')  







