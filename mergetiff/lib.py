from osgeo import gdal

def openDataset(filename):
	"""
	Opens a dataset
	"""
	return gdal.Open(filename)

def getRasterBands(dataset, bandIndices):
	"""
	Retrieves the specified raster bands from the supplied dataset
	"""
	return list([dataset.GetRasterBand(i) for i in bandIndices])

def createMergedDataset(filename, metadataDataset, rasterBands):
	"""
	Creates a new dataset with all of the metadata from the specified input dataset,
	and with each of the raster bands in the supplied list
	"""
	# Create the output dataset
	driver = gdal.GetDriverByName("GTiff")
	dataset = driver.Create(
		filename,
		rasterBands[0].XSize,
		rasterBands[0].YSize,
		len(rasterBands),
		rasterBands[0].DataType
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
