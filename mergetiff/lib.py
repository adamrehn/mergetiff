from osgeo import gdal
import numpy as np

# Private functions

def _geotiffOptions(dtype):
	"""
	Returns the driver options for creating a GeoTiff dataset of the specified type.
	"""
	
	# Use LZW compresion with all CPU cores
	options = []
	options.append("NUM_THREADS=ALL_CPUS")
	options.append("COMPRESS=LZW")
	
	# Use predictor=2 for integer types and predictor=3 for floating-point types
	if (dtype == gdal.GDT_Float32 or dtype == gdal.GDT_Float64):
		options.append("PREDICTOR=3")
	else:
		options.append("PREDICTOR=2")
	
	return options

def _numpyTypeToGdalType(dtype):
	"""
	Returns the equivalent GDAL datatype for the specified NumPy datatype
	"""
	mappings = {
		np.dtype(np.byte):    gdal.GDT_Byte,
		np.dtype(np.int8):    gdal.GDT_Byte,
		np.dtype(np.uint8):   gdal.GDT_Byte,
		np.dtype(np.int16):   gdal.GDT_Int16,
		np.dtype(np.uint16):  gdal.GDT_UInt16,
		np.dtype(np.int32):   gdal.GDT_Int32,
		np.dtype(np.uint32):  gdal.GDT_UInt32,
		np.dtype(np.float32): gdal.GDT_Float32,
		np.dtype(np.float64): gdal.GDT_Float64,
	}
	
	return mappings.get(dtype, gdal.GDT_Unknown)


# Public functions

def openDataset(filename):
	"""
	Opens a dataset
	"""
	drivers = ["GTiff"]
	options = ["NUM_THREADS=ALL_CPUS"]
	return gdal.OpenEx(filename, allowed_drivers=drivers, open_options=options)

def getRasterBands(dataset, bandIndices):
	"""
	Retrieves the specified raster bands from the supplied dataset
	"""
	return list([dataset.GetRasterBand(i) for i in bandIndices])

def getAllRasterBands(dataset):
	"""
	Retrieves all raster bands from the supplied dataset
	"""
	return list([dataset.GetRasterBand(i) for i in range(1, dataset.RasterCount + 1)])

def rasterFromFile(filename):
	"""
	Opens a dataset, reads all raster bands, and returns them as a NumPy ndarray of shape (h,w[,c])
	"""
	return rasterFromDataset(openDataset(filename))

def rasterToFile(filename, raster):
	"""
	Writes a NumPy ndarray of shape (h,w[,c]) to a GeoTiff file
	"""
	dtype = _numpyTypeToGdalType(raster.dtype)
	options = _geotiffOptions(dtype)
	dataset = datasetFromRaster(raster, False, 'GTiff', filename, options)

def rasterFromDataset(dataset):
	"""
	Reads all raster bands from a dataset and returns them as a NumPy ndarray of shape (h,w[,c])
	"""
	raster = dataset.ReadAsArray()
	if len(raster.shape) > 2:
		raster = raster.transpose((1, 2, 0))
	return raster

def datasetFromRaster(raster, forceGrayInterp = False, driver = 'MEM', filename='', options=[]):
	"""
	Takes a NumPy ndarray of shape (h,w[,c]) and creates and returns a GDAL Dataset.
	
	If forceGrayInterp is False and the image has more than three channels, the first
	four channels will have R, G, B, and Alpha colour interpretation, respectively.
	
	By default, an in-memory dataset is created using the GDAL MEM driver.
	"""
	
	# If the raster image is only single-channel, add the extra dimension to its shape
	if len(raster.shape) == 2:
		raster = raster[:,:,np.newaxis]
	
	# Create an in-memory dataset
	numBands = raster.shape[2]
	driver = gdal.GetDriverByName(driver)
	dataset = driver.Create(
		filename,
		raster.shape[1],
		raster.shape[0],
		numBands,
		_numpyTypeToGdalType(raster.dtype),
		options
	)
	
	# Copy the raster bands
	for index in range(0, raster.shape[2]):
		
		# Copy the raster data
		bandData = raster[:,:,index]
		outputBand = dataset.GetRasterBand(index+1)
		outputBand.WriteArray(bandData)
		
		# Set the colour interpretation value for the band
		colourInterp = gdal.GCI_GrayIndex
		if forceGrayInterp == False and numBands >= 3 and index <= 3:
			colourInterp = [
				gdal.GCI_RedBand,
				gdal.GCI_GreenBand,
				gdal.GCI_BlueBand,
				gdal.GCI_AlphaBand
			][index]
		outputBand.SetColorInterpretation(colourInterp)
	
	return dataset

def createMergedDataset(filename, metadataDataset, rasterBands):
	"""
	Creates a new dataset with all of the metadata from the specified input dataset,
	and with each of the raster bands in the supplied list.
	
	List items can be either gdal.Band instances or 2D NumPy arrays. In the case of
	NumPy arrays, a grayscale colour interpretation will be applied.
	"""
	
	# Create the output dataset
	driver = gdal.GetDriverByName('GTiff')
	dataset = driver.Create(
		filename,
		rasterBands[0].XSize,
		rasterBands[0].YSize,
		len(rasterBands),
		rasterBands[0].DataType,
		_geotiffOptions(rasterBands[0].DataType)
	)
	
	# Copy the metadata from the input dataset
	if metadataDataset != None:
		dataset.SetGeoTransform( metadataDataset.GetGeoTransform() )
		dataset.SetProjection( metadataDataset.GetProjection() )
		dataset.SetMetadata( metadataDataset.GetMetadata() )
	
	# Copy the GCPs from the input dataset, if it has any
	if metadataDataset != None and metadataDataset.GetGCPCount() > 0:
		dataset.SetGCPs( metadataDataset.GetGCPs(), metadataDataset.GetGCPProjection() )
	
	# Copy each of the input raster bands
	for index, inputBand in enumerate(rasterBands):
		
		# Retrieve the output band
		outputBand = dataset.GetRasterBand(index+1)
		
		# If the input band is a 2D NumPy array, copy the raster data and interpret it as grayscale
		if not hasattr(inputBand, 'ReadAsArray'):
			outputBand.WriteArray(inputBand)
			outputBand.SetColorInterpretation(gdal.GCI_GrayIndex)
			continue
		
		# Copy the band data
		outputBand.WriteArray( inputBand.ReadAsArray() )
		
		# Copy the "no data" sentinel value, if any
		if inputBand.GetNoDataValue() != None:
			outputBand.SetNoDataValue( inputBand.GetNoDataValue() )
		
		# Copy the colour interpretation value, if any
		if inputBand.GetColorInterpretation() != None:
			outputBand.SetColorInterpretation( inputBand.GetColorInterpretation() )
	
	return dataset
