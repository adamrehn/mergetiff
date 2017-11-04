from __future__ import print_function
from .lib import *
import os, sys

def main():
	
	# Check that the required command-line arguments have been supplied
	if len(sys.argv) > 3 and len(sys.argv) % 2 == 0:
		
		# Parse the command-line arguments
		outputFile = sys.argv[1]
		datasets = []
		bands = []
		for i in range(2, len(sys.argv), 2):
			dataset = openDataset(sys.argv[i])
			bandStr = sys.argv[i+1]
			bandIndices = [] if bandStr == '-' else [int(b) for b in bandStr.split(',')]
			datasets.append(dataset)
			bands.extend(getRasterBands(dataset, bandIndices))
		
		# Attempt to create the merged dataset
		createMergedDataset(outputFile, datasets[0], bands)
		print('Created merged dataset "' + outputFile + '".')
		
	else:
		print('Usage:')
		print(os.path.basename(sys.argv[0]) + ' <OUT.TIF> <IN1.TIF> <BAND1,BAND2,BAND3> [<IN2.TIF> <BAND1,BAND2,BAND3>]')
