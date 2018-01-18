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
	options.append("BIGTIFF=IF_SAFER")
	
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

def _gdalTypeToNumpyType(dtype):
	"""
	Returns the equivalent NumPy datatype for the specified GDAL datatype
	"""
	mappings = {
		gdal.GDT_Byte:    np.dtype(np.uint8),
		gdal.GDT_Int16:   np.dtype(np.int16),
		gdal.GDT_UInt16:  np.dtype(np.uint16),
		gdal.GDT_Int32:   np.dtype(np.int32),
		gdal.GDT_UInt32:  np.dtype(np.uint32),
		gdal.GDT_Float32: np.dtype(np.float32),
		gdal.GDT_Float64: np.dtype(np.float64)
	}
	
	return mappings.get(dtype, np.dtype(float))

def _memWrapFilename(raster):
	"""
	Generates the GDAL filename to create an in-memory dataset that wraps a NumPy array.
	"""
	
	# Verify that the NumPy's memory is contiguous
	if raster.flags['C_CONTIGUOUS'] != True:
		raise RuntimeError('NumPy array must be row-major and contiguous')
	
	# Retrieve the underlying pointer for the NumPy array
	pointer, read_only_flag = raster.__array_interface__['data']
	
	# Retrieve the image dimensions
	rows  = raster.shape[0]
	cols  = raster.shape[1]
	bands = raster.shape[2] if len(raster.shape) > 2 else 1
	
	# Build the filename for the memory-wrap dataset
	return 'MEM:::DATAPOINTER={},PIXELS={},LINES={},BANDS={},DATATYPE={},PIXELOFFSET={},LINEOFFSET={},BANDOFFSET={}'.format(
		hex(pointer),
		cols,
		rows,
		bands,
		gdal.GetDataTypeName(_numpyTypeToGdalType(raster.dtype)),
		bands * raster.dtype.itemsize,
		cols * bands * raster.dtype.itemsize,
		raster.dtype.itemsize
	)

def _vrtWrapBand(vrtDataset, sourceBand):
	"""
	Wraps a GDAL raster band in a VRT band.
	"""
	
	# Retrieve the width and height from the source band
	width = sourceBand.XSize
	height = sourceBand.YSize
	
	# Create the new VRT raster band
	vrtDataset.AddBand(sourceBand.DataType)
	vrtBand = vrtDataset.GetRasterBand(vrtDataset.RasterCount)
	
	# Build the XML for the data source
	bandSource = '''<SimpleSource>
		<SourceFilename relativeToVRT="1">{}</SourceFilename>
		<SourceBand>{}</SourceBand>
		<SrcRect xOff="{}" yOff="{}" xSize="{}" ySize="{}"/>
		<DstRect xOff="{}" yOff="{}" xSize="{}" ySize="{}"/>
	</SimpleSource>'''.format(
		sourceBand.GetDataset().GetFileList()[0],
		sourceBand.GetBand(),
		0, 0, width, height,
		0, 0, width, height
	)
	
	# Add the data source to the VRT band
	metadata = {}
	metadata['source_0'] = bandSource
	vrtBand.SetMetadata(metadata, 'vrt_sources')
	return vrtBand

def _vrtWrapArray(vrtDataset, raster):
	"""
	Wraps a 2D NumPy array in a VRT band.
	"""
	
	# Retrieve the width and height from the NumPy array
	width = raster.shape[1]
	height = raster.shape[0]
	
	# Create the new VRT raster band
	vrtDataset.AddBand(_numpyTypeToGdalType(raster.dtype))
	vrtBand = vrtDataset.GetRasterBand(vrtDataset.RasterCount)
	
	# Build the XML for the data source
	bandSource = '''<SimpleSource>
		<SourceFilename>{}</SourceFilename>
		<SourceBand>{}</SourceBand>
		<SrcRect xOff="{}" yOff="{}" xSize="{}" ySize="{}"/>
		<DstRect xOff="{}" yOff="{}" xSize="{}" ySize="{}"/>
	</SimpleSource>'''.format(
		_memWrapFilename(raster),
		1,
		0, 0, width, height,
		0, 0, width, height
	)
	print(bandSource)
	# Add the data source to the VRT band
	metadata = {}
	metadata['source_0'] = bandSource
	vrtBand.SetMetadata(metadata, 'vrt_sources')
	return vrtBand


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

def wrapRasterData(raster):
	"""
	Wraps a NumPy array in a GDAL in-memory dataset. The memory is only wrapped, no copy is made.
	"""
	return gdal.Open(_memWrapFilename(raster), gdal.GA_ReadOnly)

def createMergedDataset(filename, metadataDataset, rasterBands, progressCallback=None):
	"""
	Creates a new dataset with all of the metadata from the specified input dataset,
	and with each of the raster bands in the supplied list.
	
	List items can be either gdal.Band instances or 2D NumPy arrays. In the case of
	NumPy arrays, a grayscale colour interpretation will be applied.
	
	Do NOT wrap NumPy arrays in GDAL datasets using wrapRasterData() and pass the bands
	of these datasets to this function - instead pass the NumPy arrays directly.
	
	A callback can be specified to be notified of progress. The callback should adhere to
	the standard GDALProgressFunc signature:
	
	`callback(dfComplete, message, arg)`
	
	The callback should return 1 if processing should continue, or 0 to cancel processing.
	(See <https://github.com/OSGeo/gdal/blob/trunk/gdal/doc/api.dox> for details.)
	"""
	
	# Determine resolution and datatype information from the first raster band
	# (How we extract this depends on whether it is a gdal.Band instance or 2D NumPy array)
	if hasattr(rasterBands[0], 'ReadAsArray'):
		width  = rasterBands[0].XSize
		height = rasterBands[0].YSize
		dtype  = rasterBands[0].DataType
	else:
		width  = rasterBands[0].shape[1]
		height = rasterBands[0].shape[0]
		dtype  = _numpyTypeToGdalType(rasterBands[0].dtype)
	
	# Create a virtual dataset
	virtualDataset = gdal.GetDriverByName('VRT').Create('', width, height, 0)
	
	# Copy the metadata from the input dataset
	if metadataDataset != None:
		virtualDataset.SetGeoTransform( metadataDataset.GetGeoTransform() )
		virtualDataset.SetProjection( metadataDataset.GetProjection() )
		virtualDataset.SetMetadata( metadataDataset.GetMetadata() )
	
	# Copy the GCPs from the input dataset, if it has any
	if metadataDataset != None and metadataDataset.GetGCPCount() > 0:
		virtualDataset.SetGCPs( metadataDataset.GetGCPs(), metadataDataset.GetGCPProjection() )
	
	# Assign each of the input raster bands as the source for the corresponding virtual band
	for index, inputBand in enumerate(rasterBands):
		
		# Determine if the input band is a 2D NumPy array or a GDAL band, and wrap it accordingly
		if not hasattr(inputBand, 'ReadAsArray'):
			outputBand = _vrtWrapArray(virtualDataset, inputBand)
			outputBand.SetColorInterpretation(gdal.GCI_GrayIndex)
			continue
		else:
			outputBand = _vrtWrapBand(virtualDataset, inputBand)
		
		# Copy the "no data" sentinel value, if any
		if inputBand.GetNoDataValue() != None:
			outputBand.SetNoDataValue( inputBand.GetNoDataValue() )
		
		# Copy the colour interpretation value, if any
		if inputBand.GetColorInterpretation() != None:
			outputBand.SetColorInterpretation( inputBand.GetColorInterpretation() )
	
	# Attempt to create the output dataset as a copy of the virtual dataset
	driver = gdal.GetDriverByName('GTiff')
	dataset = driver.CreateCopy(
		filename,
		virtualDataset,
		0,
		_geotiffOptions(dtype),
		progressCallback
	)
	
	return dataset


# Public classes

class RasterReader(object):
	"""
	Provides functionality to read raster data from a dataset, storing all
	raster data in memory if there is sufficient memory available, or else
	reading data from file as needed when the dataset is too large.
	"""
	
	def __init__(self, filename):
		
		# Attempt to open the dataset
		self._dataset = openDataset(filename)
		
		# Retrieve the image dimensions
		self._width  = self._dataset.GetRasterBand(1).XSize
		self._height = self._dataset.GetRasterBand(1).YSize
		
		# Create our `shape` attribute
		channels = self._dataset.RasterCount
		if channels > 1:
			self.shape = (self._height, self._width, channels)
		else:
			self.shape = (self._height, self._width)
		
		# Attempt to read the raster data into memory
		try:
			self._raster = rasterFromDataset(self._dataset)
		except MemoryError:
			self._raster = None
	
	
	def isInMemory(self):
		"""
		Determines if the raster data is currently stored in system memory.
		"""
		return self._raster is not None
	
	
	def width(self):
		"""
		Returns the width of the raster data.
		"""
		return self._width
	
	
	def height(self):
		"""
		Returns the height of the raster data.
		"""
		return self._height
	
	
	def _assert_slice(self, obj):
		if type(obj) != type(slice(None)):
			raise TypeError('indices must be slices')
	
	
	def __getitem__(self, key):
		
		# Verify that the specified key is either a slice or tuple of slices
		if type(key) == type(tuple()):
			for item in key:
				self._assert_slice(item)
		else:
			self._assert_slice(key)
		
		# If the raster data is already in memory, simply index into the NumPy array
		if self.isInMemory() == True:
			return self._raster[key]
		else:
			
			# Any unspecified slices will be treated as empty
			ySlice = slice(None, None, None)
			xSlice = slice(None, None, None)
			cSlice = slice(None, None, None)
			
			# Determine how many slices were specified and unpack them
			if type(key) != type(tuple()):
				ySlice = key
			elif len(key) == 2:
				ySlice, xSlice = key
			elif len(key) == 3:
				ySlice, xSlice, cSlice = key
			else:
				raise RuntimeError('only 3 slice dimensions are supported')
			
			# Determine the X and Y image coordinates
			xStart = xSlice.start if xSlice.start is not None else 0
			yStart = ySlice.start if ySlice.start is not None else 0
			xEnd = xSlice.stop if xSlice.stop is not None else self._width
			yEnd = ySlice.stop if ySlice.stop is not None else self._height
			xSize = xEnd - xStart
			ySize = yEnd - yStart
			
			# Read the raster data from file
			data = self._dataset.ReadAsArray(xoff=xStart, yoff=yStart, xsize=xSize, ysize=ySize)
			
			# If the image has multiple raster bands, apply the channel slice
			if len(data.shape) > 2:
				data = data.transpose((1, 2, 0))
				data = data[:, :, cSlice]
			
			return data
