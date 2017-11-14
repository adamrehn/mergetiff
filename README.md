`mergetiff` GeoTiff Raster Merging Tool
=======================================

This package implements a library and associated command-line tool called `mergetiff` that provides functionality to merge raster bands from multiple GeoTiff files into a single dataset. Metadata (including geospatial reference and projection data) will be copied from the first input dataset (when using the command-line tool) or from the dataset passed as the second argument to the `createMergedDataset()` function.

Functionality is also provided for converting between GDAL datasets and NumPy arrays, to facilitate interoperability with other image processing libraries.


Contents
--------

- [Requirements](#requirements)
- [Installing the GDAL 2.x Python bindings](#installing-the-gdal-2x-python-bindings)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Ubuntu 14.04 LTS or Ubuntu 16.04 LTS](#ubuntu-1404-lts-or-ubuntu-1604-lts)
  - [Ubuntu 17.04 and newer](#ubuntu-1704-and-newer)
- [Installation](#installation)
- [Using the command-line tool](#using-the-command-line-tool)
- [Using the library](#using-the-library)


Requirements
------------

- Python 2.7 or Python 3.4+
- Python bindings for GDAL 2.0+
- NumPy


Installing the GDAL 2.x Python bindings
---------------------------------------


### Windows

GDAL binary wheels for Windows are maintained by Christoph Gohlke and can be downloaded from <https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal>.


### macOS

OSGeo maintains a [Homebrew tap](https://github.com/OSGeo/homebrew-osgeo4mac) which provides packages that can be installed via [Homebrew](https://brew.sh/):

```
brew tap osgeo/osgeo4mac
brew install gdal2
brew link --force gdal2
pip install gdal
```


### Ubuntu 14.04 LTS or Ubuntu 16.04 LTS

The official package repositories for these older Ubuntu versions only contain GDAL 1.x. GDAL 2.x can be installed via the [UbuntuGIS PPA](https://launchpad.net/~ubuntugis/+archive/ubuntu/ppa):

```
sudo add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
sudo apt update 
sudo apt install gdal-bin python-gdal python3-gdal
```


#### Ubuntu 17.04 and newer

The official package repositories for newer Ubuntu versions already contain GDAL 2.x, making it extremely simple to install:

```
sudo apt install gdal-bin python-gdal python3-gdal
```


Installation
------------

Once the GDAL Python bindings have been installed, `mergetiff` can be installed by simply running:

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
