# -*- coding: utf-8 -*-
from datetime import datetime
import statistics
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.ticker as ticker
import glob
import os
import numpy as np
import sys
import re

def main():
	#Get kit and if there is a standard curve
	quantArgs = 'C:\\Tecan\\Variables\\QuantITargs.txt'
	ascPath = 'C:\\Users\\Public\\Documents\\Tecan\\Magellan\\asc\\*'

	with open(quantArgs, 'r') as argsFile:
		lines = argsFile.readlines()

		header = re.sub( '\"', '', lines[0].strip() ).split(';')
		line = re.sub( '\"', '', lines[1].strip() ).split(';')

		args = {}

		for i in range(0, len(header)):
			args[header[i]] = line[i]

	# Set parameters for standard curve
	date = str(datetime.now().strftime("%Y%m%d-%H%M%S"))
	storedStdCurve = 'C:\\Tecan\\Variables\\StdCurves\\%sStdCurve.txt' % args['QuantITkit']
	storedStdCurveBackUp = 'C:\\Tecan\\Variables\\StdCurves\\%sStdCurve-BackUp.txt' % args['QuantITkit']
	stdCurvePNGpath = 'C:\\Tecan\\Variables\\StdCurves\\%sStdCurve-%s.png' % (args['QuantITkit'], date)
	concPath = 'C:\\Tecan\\Variables\\ConcGrids\\%sConcGrid-%s.png' % (args['QuantITkit'], date)
	resultFile = 'C:\\Users\\Hp\\Desktop\\MagellanConcentrations\\' + args['QuantITkit'] + '-' + date + '.csv'
	concFailedPath = 'C:\\Tecan\\Variables\\ConcGrids\\concGrid.png'
	stdFailedPath = 'C:\\Tecan\\Variables\\StdCurves\\stdCurve.png'

	# Get the latest measurement file from magellan
	ascFiles = glob.glob(ascPath)
	latestFile = max(ascFiles, key=os.path.getctime)

	# Read in data
	position = []
	dilutionFactors = []
	rawData = []

	with open(latestFile, 'r') as file:
		for line in file:
			if not line.startswith('Date'): # Get lines with measurement
				# Remove parenthes
				line = re.sub('\(|\)','',line)
				row = line.strip().split(',')
				position.append(row[0])

				try:
					dilutionFactors.append(int(row[1]))
					rawData.append(int(row[2]))

				except:
					concPath = concFailedPath
					stdCurvePNGpath = stdFailedPath
					sys.exit("Error: Failed to read raw data")

			else:
				magellanDate = line.strip()
				method = next(file).strip()

	# Calculate std. curve or read in old
	if args['stdCurve'] == 'No': # Calculate new standard curve
		stdDate = date

		if args['QuantITkit'] == 'HighSensitivity':
			standards = [ float(x) for x in [0,0.5,1,2,4,6,8,10] ]
		elif args['QuantITkit'] == 'BroadRange':
			standards = [ int(x) for x in [0,5,10,20,40,60,80,100] ]

		#calculate linear equation from first column, standards
		x = [rawData[0],rawData[12],rawData[24],rawData[36],rawData[48],rawData[60],rawData[72],rawData[84]]

		# Blank reduction
		x = [a - x[0] for a in x]

		xAvg = statistics.mean(x)
		yAvg = statistics.mean(standards)
		xySum = sum([(x - xAvg)*(y - yAvg) for x,y in  zip(x, standards)])
		xxSum = sum([(x - xAvg)*(x - xAvg) for x in x])

		transformationFactor = xySum/xxSum
		blank = rawData[0]

		# Get concentration for standards
		y = [a*transformationFactor for a in x]

		# Calculate R2-value
		SSres = sum([(f-y)*(f-y) for f,y in zip(standards,y)])
		R2 = 1 - SSres/xxSum

		# Write new standard curve
		with open(storedStdCurve, 'w') as file:
			with open(storedStdCurveBackUp, 'a') as backupFile:
				

				if args['QuantITkit'] == "BroadRange":
					file.write('Date;Slope;Blank;Raw;BRstdCurvePNG;R2\n')
				elif args['QuantITkit'] == "HighSensitivity":
					file.write('Date;Slope;Blank;Raw;HSstdCurvePNG;R2\n')
				else:
					concPath = concFailedPath
					stdCurvePNGpath = stdFailedPath
					sys.exit("Error: Failed to read raw data")

				file.write('\"%s\";%f;%d;%s;\"%s\";%f' % (stdDate, transformationFactor, blank, x, stdCurvePNGpath, R2))
				backupFile.write('\n\"%s\";%f;%d;%s;\"%s\";%f' % (stdDate, transformationFactor, blank, x, stdCurvePNGpath, R2))

		# Set dilution for standards to one
		dilutionFactors[0] = 1
		dilutionFactors[12] = 1
		dilutionFactors[24] = 1
		dilutionFactors[36] = 1
		dilutionFactors[48] = 1
		dilutionFactors[60] = 1
		dilutionFactors[72] = 1
		dilutionFactors[84] = 1

		# Plot the new standard
		stdX = [0,(standards[7]/transformationFactor)]
		stdY = [0,standards[7]]
		plt.plot(stdX, stdY, color = 'red')
		plt.plot(x,standards, 'o', color = 'blue')
		plt.title('%s standard curve %s' % (args['QuantITkit'], stdDate))
		plt.xlabel('Raw data')
		plt.ylabel('Concentration [ng/ul]')
		plt.savefig(stdCurvePNGpath)
		plt.close()

	elif args['stdCurve'] == 'Yes':
		#read in slope and blank
		with open(storedStdCurve, 'r') as file:
			lines = file.readlines()
			line2 = lines[1].split(';')
			stdDate = line2[0].strip('\"')
			transformationFactor = float(line2[1])
			blank = int(line2[2])
			R2 = float(line2[5])
			stdCurvePNGpath = line2[4].strip('\"')

	else:
		concPath = concFailedPath
		stdCurvePNGpath = stdFailedPath
		sys.exit("Error: Failed to read raw data")

	# Write results to csv
	concData = ['']*96

	with open(resultFile, 'w') as outFile:
		outFile.write('well,dilution,raw,concentration[ng/ul]\n') # Header

		for well in range(0,96):
			dataBlankReduct = rawData[well] - blank
			concData[well] = dataBlankReduct*transformationFactor*dilutionFactors[well]

			if concData[well] < 0:
				concData[well] = 0

			outFile.write('%s,%s,%d,%f\n' % (position[well], dilutionFactors[well], rawData[well], concData[well]))

		outFile.write('\nMethod: %s\nKit: %s\nOld standard curve: %s\nStandard Curve Calculation Date: %s\n' % (method, args['QuantITkit'], args['stdCurve'], stdDate))
		outFile.write('transformationFactor: %f\nBlank: %d\nR2: %f\n\n' % (transformationFactor, blank, R2))
		outFile.write('Workflow: %s\nUser: %s\nNumber of Samples: %s\n' % (args['Workflow'], args['CurrentUserInput'], args['NumberOfSamples']))
		outFile.write('%s\nDate and time of calculations: %s\n' % (magellanDate, date))

	# Display concentrations in grid
	# Arange data in a matrix
	z = np.array( [ np.array(concData[0:12]), np.array(concData[12:24]),np.array(concData[24:36]), np.array(concData[36:48]),
		np.array(concData[48:60]), np.array(concData[60:72]),np.array(concData[72:84]), np.array(concData[84:96]) ],dtype = np.float64 )

	# Make a new matrix with values between 0 and 1 for color
	concMax = max(concData)
	zColor = np.divide(z,concMax)

	for i in range(0,8):
		for n in range (0,12):
			if zColor[i][n] < 0:
				zColor[i][n] = 0

	# Make figure with colored grid
	fig, ax = plt.subplots(figsize=(9,6))
	ax.imshow(z)

	# Write concentration values grid
	for val in range(0,96):
		xval = int(np.floor(val/12))
		yval = int(val - xval*12)

		zval = concData[val]
		t = ("%.2f" % zval)
		c = 'w' if zval < 0.25*concMax else 'k'
		ax.text(yval,xval,t,color=c,va='center',ha='center')
	xlabels = ['1','2','3','4','5','6','7','8','9','10','11','12']
	ylabels = ['A','B','C','D','E','F','G','H']

	# Add centered labels
	indx,indy = np.arange(12),np.arange(8)
	ax.set_xticks(indx + 0.5)
	ax.set_yticks(indy + 0.5)
	ax.grid(ls='-', lw=2)

	for a, ind, labels in zip((ax.xaxis, ax.yaxis), (indx, indy), (xlabels, ylabels)):
		a.set_major_formatter(ticker.NullFormatter())
		a.set_minor_locator(ticker.FixedLocator(ind))
		a.set_minor_formatter(ticker.FixedFormatter(labels))

	ax.xaxis.tick_top()
	plt.savefig(concPath)
	plt.close()

	with open(quantArgs, 'w') as pathfile:
		argsLines = [[],[]]
		for head in args:
			argsLines[0].append(head)
			argsLines[1].append(args[head])

		pathfile.write(';'.join(argsLines[0][0:5]) + ';ConcentrationPNG;stdCurvePNG\n')
		pathfile.write('\"' + '\";\"'.join(argsLines[1][0:5]) + '\";\"%s\";\"%s\"' % (concPath,stdCurvePNGpath))

	print('Done!')

if __name__ == "__main__":
	main()
