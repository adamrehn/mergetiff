`mergetiff` GeoTiff Raster Merging Tool
=======================================

This package implements a library and associated command-line tool called `mergetiff` that provides functionality to merge raster bands from multiple GeoTiff files into a single dataset. Metadata (including geospatial reference and projection data) will be copied from the first input dataset (when using the command-line tool) or from the dataset passed as the second argument to the `createMergedDataset()` function.

Functionality is also provided for converting between GDAL datasets and NumPy arrays, to facilitate interoperability with other image processing libraries.


Requirements
------------

- Python 2.7 or Python 3.4+
- GDAL Python bindings
- NumPy


Installation
------------

To install, run:

```
pip install mergetiff
```


Using the command-line tool
---------------------------

If we have one GeoTiff called `rgb.tif` containing 3 raster bands and another GeoTiff called `alpha.tif` containing a single raster band, we can merge them by running: 

```
mergetiff out.tif rgb.tif 1,2,3 alpha.tif 1
```

Alternatively, if we only want to copy the metadata from the first file without including any of its raster bands, the band specifier `-` can be used to exclude all bands:

```
mergetiff out.tif rgb.tif - alpha.tif 1
```

This will copy all of the metadata from `rgb.tif` and the first raster band from `alpha.tif` into the output file.


Using the library
-----------------

To perform the same merge described in the section above using the library directly:

```
import mergetiff

# Open both datasets
dataset1 = mergetiff.openDataset('rgb.tif')
dataset2 = mergetiff.openDataset('alpha.tif')

# Include the raster bands that we want
# (Note that the dataset we use for metadata does not have to be included)
bands = []
bands.extend( mergetiff.getRasterBands(dataset1, [1,2,3]) )
bands.extend( mergetiff.getRasterBands(dataset2, [1]) )

# Perform the merge, using the metadata from the first dataset
mergetiff.createMergedDataset('merged.tif', dataset1, bands)
```

If we want to perform image processing on raster data, we can use the NumPy interoperability functionality of the library:

```
import mergetiff

# Open the dataset and read the raster data into a NumPy ndarray
dataset = mergetiff.openDataset('rgb.tif')
rasterArray = mergetiff.rasterFromDataset(dataset)

# Manipulate the raster array here
# ...

# Convert the modified raster data back into a GDAL dataset
modifiedDataset = mergetiff.datasetFromRaster(rasterArray)

# Merge the modified raster bands with the original metadata
bands = mergetiff.getRasterBands(modifiedDataset, [1,2,3])
mergetiff.createMergedDataset('modified.tif', dataset, bands)
```
