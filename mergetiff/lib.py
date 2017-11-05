from osgeo import gdal
import numpy as np

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

def rasterFromFile(filename):
	"""
	Opens a dataset, reads all raster bands, and returns them as a NumPy ndarray of shape (h,w[,c])
	"""
	return rasterFromDataset(openDataset(filename))

def rasterFromDataset(dataset):
	"""
	Reads all raster bands from a dataset and returns them as a NumPy ndarray of shape (h,w[,c])
	"""
	raster = dataset.ReadAsArray()
	if len(raster.shape) > 2:
		raster = raster.transpose((1, 2, 0))
	return raster

def datasetFromRaster(raster, forceGrayInterp = False):
	"""
	Takes a NumPy ndarray of shape (h,w[,c]) and returns an in-memory GDAL Dataset
	"""
	
	# If the raster image is only single-channel, add the extra dimension to its shape
	if len(raster.shape) == 2:
		raster = raster[:,np.newaxis]
	
	# Mappings from NumPy datatypes to their equivalent GDAL datatypes
	typeMappings = {
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
	
	# Create an in-memory dataset
	numBands = raster.shape[2]
	driver = gdal.GetDriverByName('MEM')
	dataset = driver.Create(
		'',
		raster.shape[1],
		raster.shape[0],
		numBands,
		typeMappings[raster.dtype]
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
	and with each of the raster bands in the supplied list
	"""
	
	# Use LZW compresion with all CPU cores
	options = []
	options.append("NUM_THREADS=ALL_CPUS")
	options.append("COMPRESS=LZW")
	
	# Use predictor=2 for integer types and predictor=3 for floating-point types
	if (rasterBands[0].DataType == gdal.GDT_Float32 or rasterBands[0].DataType == gdal.GDT_Float64):
		options.append("PREDICTOR=3")
	else:
		options.append("PREDICTOR=2")
	
	# Create the output dataset
	driver = gdal.GetDriverByName('GTiff')
	dataset = driver.Create(
		filename,
		rasterBands[0].XSize,
		rasterBands[0].YSize,
		len(rasterBands),
		rasterBands[0].DataType,
		options
	)
	
	# Copy the metadata from the input dataset
	dataset.SetGeoTransform( metadataDataset.GetGeoTransform() )
	dataset.SetProjection( metadataDataset.GetProjection() )
	dataset.SetMetadata( metadataDataset.GetMetadata() )
	
	# Copy the GCPs from the input dataset, if it has any
	if metadataDataset.GetGCPCount() > 0:
		dataset.SetGCPs( metadataDataset.GetGCPs(), metadataDataset.GetGCPProjection() )
	
	# Copy each of the input raster bands
	for index, inputBand in enumerate(rasterBands):
		
		# Copy the raster data
		outputBand = dataset.GetRasterBand(index+1)
		outputBand.WriteArray( inputBand.ReadAsArray() )
		
		# Copy the "no data" sentinel value, if any
		if inputBand.GetNoDataValue() != None:
			outputBand.SetNoDataValue( inputBand.GetNoDataValue() )
		
		# Copy the colour interpretation value, if any
		if inputBand.GetColorInterpretation() != None:
			outputBand.SetColorInterpretation( inputBand.GetColorInterpretation() )
