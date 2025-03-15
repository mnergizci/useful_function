#!/usr/bin/env python

import sys
import rioxarray as r
import numpy as np

# Ensure correct number of arguments
if len(sys.argv) != 10:
    print("Usage: if_remove_tide_correction.py ifile g1f g2f t1f t2f i1f i2f ext ofile")
    print("(ext should be either 'diff_pha', 'diff_unfiltered_pha', or 'unw')")
    sys.exit(1)

# Read command-line arguments
ifile, g1f, g2f, t1f, t2f, i1f, i2f, ext, ofile = sys.argv[1:]

# Load raster files
try:
    i = r.open_rasterio(ifile).squeeze()  # Interferogram
    g1 = r.open_rasterio(g1f).squeeze()   # GACOS correction 1
    g2 = r.open_rasterio(g2f).squeeze()   # GACOS correction 2
    t1 = r.open_rasterio(t1f).squeeze()   # SET correction 1
    t2 = r.open_rasterio(t2f).squeeze()   # SET correction 2
    i1 = r.open_rasterio(i1f).squeeze()   # Ionospheric correction 1
    i2 = r.open_rasterio(i2f).squeeze()   # Ionospheric correction 2
except Exception as e:
    print(f"Error loading raster files: {e}")
    sys.exit(1)

# Ensure all grids have the same shape
shapes = [i.shape, g1.shape, g2.shape, t1.shape, t2.shape, i1.shape, i2.shape]
if not all(s == i.shape for s in shapes):
    print(f"Error: Grid sizes do not match! Expected {i.shape}, but got:")
    print(f"g1: {g1.shape}, g2: {g2.shape}, t1: {t1.shape}, t2: {t2.shape}, i1: {i1.shape}, i2: {i2.shape}")
    sys.exit(1)

# Check for NaN-only files
for var, name in zip([i, g1, g2, t1, t2, i1, i2], [ifile, g1f, g2f, t1f, t2f, i1f, i2f]):
    if np.isnan(var.values).all():
        print(f"Error: {name} contains only NaN values.")
        sys.exit(1)

# Convert zeros to NaN for all arrays
i = i.where(i != 0, np.nan)
g1 = g1.where(g1 != 0, np.nan)
g2 = g2.where(g2 != 0, np.nan)
t1 = t1.where(t1 != 0, np.nan)
t2 = t2.where(t2 != 0, np.nan)
i1 = i1.where(i1 != 0, np.nan)
i2 = i2.where(i2 != 0, np.nan)

# Compute corrections
dg = g2 - g1  # GACOS correction
dt = (t1 - t2) * 226.56  # Convert meters to radians (SET correction)
di = i1 - i2  # Ionospheric correction

# Apply corrections step by step
i_gacos_corrected = i - dg
i_gacos_set_corrected = i_gacos_corrected - dt
i_gacos_set_iono_corrected = i_gacos_set_corrected - di

# If the interferogram is wrapped, apply phase wrapping
if ext != 'unw':
    print('Wrapping phase between -π and π')
    i_gacos_set_iono_corrected.values = np.angle(np.exp(1j * i_gacos_set_iono_corrected.values))

# Save corrected raster
i_gacos_set_iono_corrected.rio.to_raster(ofile)

print(f"Correction applied and saved to {ofile}")
