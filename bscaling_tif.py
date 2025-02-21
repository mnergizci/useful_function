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

'''
This code helps to scaling factor boi and save the metadata file
Nergizci 05/11/2024
'''

if len(sys.argv) < 1:
    print('Please provide pair information (assuming you run this in your BATCH_CACHE_DIR/frame)')
    print('e.g. python bscaling_tif.py 20230129_20230210')
    sys.exit(1)


##variables
tempdir = os.getcwd()
frame = os.path.basename(tempdir)
framedir = tempdir
pair=sys.argv[1]
prime, second = pair.split('_')
tr= int(frame[:3])
GEOC_folder=os.path.join(framedir, 'GEOC')
RSLC_folder=os.path.join(framedir, 'RSLC')

tif=os.path.join(GEOC_folder,pair,pair+'.geo.bovldiff.adf.tif')
outtif=os.path.join(GEOC_folder,pair,pair+'.geo.boi_scaling.tif')

if not os.path.exists(tif):
    print('the file does not exist here, trying to find it in batchdir')
    batch=os.environ['BATCH_CACHE_DIR']
    tif=os.path.join(batch,frame,'GEOC',pair,pair+'.geo.bovldiff.adf.tif')
    outtif = os.path.join(batch, frame,'GEOC',pair,pair+'.geo.boi_scaling.tif')

if not os.path.exists(tif):
    print('ERROR, the file does not exist in:')
    print(tif)
    exit()


metafile = os.path.join(os.environ['LiCSAR_public'], str(tr), frame, 'metadata', 'metadata.txt')
primepoch = misc.grep1line('master=',metafile).split('=')[1]
path_to_slcdir = os.path.join(os.environ['LiCSAR_procdir'], str(tr), frame, 'SLC', primepoch)

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

print('dfDCs have been calculated, please wait....')

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







