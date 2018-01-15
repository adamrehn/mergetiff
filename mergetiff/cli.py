from __future__ import print_function
import os, sys, time
from .lib import *

def displayProgress(percent, currBand, totalBands, currBlock, totalBlocks, blocksize):
	sys.stdout.write('{:.0f}% complete (Processing band {}/{}, block {}/{}, using blocksize {})\r'.format(
		percent,
		currBand,
		totalBands,
		currBlock,
		totalBlocks,
		blocksize
	))
	sys.stdout.flush()

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
		startTime = time.time()
		createMergedDataset(outputFile, datasets[0], bands, displayProgress)
		endTime = time.time()
		print('100% complete (Processed all blocks of all bands)                               ')
		print('Created merged dataset "{}" in {:.2f} seconds.'.format(outputFile, (endTime - startTime)))
		
	else:
		print('Usage:')
		print(os.path.basename(sys.argv[0]) + ' <OUT.TIF> <IN1.TIF> <BAND1,BAND2,BAND3> [<IN2.TIF> <BAND1,BAND2,BAND3>]')
