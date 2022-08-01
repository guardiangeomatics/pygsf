#name:			pygsfConditioner
#created:		April 2017
#by:			p.kennedy@fugro.com
#description:	python module to pre-process a gsf sonar file and do useful hings with it
#				See readme.md for more details

import csv
import sys
import time
import os
import fnmatch
import math
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from datetime import datetime
from datetime import timedelta
from glob import glob
import pygsf
import struct

###############################################################################
def main():
	parser = ArgumentParser(description='Read gsf file and condition the file by removing redundant records and injecting updated information to make the file self-contained.',
			epilog='Example: \n To condition a single file use -i c:/temp/myfile.gsf -exclude 12 \n to condition gsf files in a folder use -i c:/temp/*.gsf\n To condition gsf .gsf files recursively in a folder, use -r -i c:/temp \n To condition all .gsf files recursively from the current folder, use -r -i ./ \n', formatter_class=RawTextHelpFormatter)
	parser.add_argument('-exclude', dest='exclude', action='store', default="", help='Exclude these records.  Note: this needs to be case sensitive e.g. -exclude 12,22')
	parser.add_argument('-dump', action='store_true', default=False, dest='dump', help='Ascii Dump of the GSF file. [Default: False]')
	parser.add_argument('-extractbs', action='store_true', default=False, dest='extractbs', help='Extract backscatter from snippet so we can analyse. [Default: False]')
	parser.add_argument('-i', dest='inputFile', action='store', help='Input gsf filename. It can also be a wildcard, e.g. *.gsf')
	parser.add_argument('-o', dest='outputFile', action='store', help='Output gsf filename. If not supplied, a filename is auto generated. [Default = ""')
	parser.add_argument('-odir', dest='odir', action='store', default="", help='Specify a relative output folder e.g. -odir conditioned')
	parser.add_argument('-r', action='store_true', default=False, dest='recursive', help='Search recursively from the current folder.  [Default: False]')

	if len(sys.argv)==1:
		parser.print_help()
		sys.exit(1)
		
	args = parser.parse_args()

	fileCounter=0
	matches = []
	extractBackscatter = False
	writeConditionedFile = False
	dump = False
	latitude = 0
	longitude = 0
	exclude = []

	if args.dump:
		dump = args.dump

	if args.recursive:
		for root, dirnames, filenames in os.walk(os.path.dirname(args.inputFile)):
			for f in fnmatch.filter(filenames, '*.gsf'):
				matches.append(os.path.join(root, f))
				print (matches[-1])
	else:
		if os.path.exists(args.inputFile):
			matches.append (os.path.abspath(args.inputFile))
		else:
			for filename in glob(args.inputFile):
				matches.append(filename)
		print (matches)

	if len(matches) == 0:
		print ("Nothing found in %s to condition, quitting" % args.inputFile)
		exit()

	if len(args.exclude) > 0:
		exclude = list(map(int, args.exclude.split(",")))
		print ("Excluding datagrams: %s :" % exclude)

	# if args.extractbs:
	# 	extractBackscatter = True
	# 	writeConditionedFile= False #we do not need to write out a .gsf file
	# 	# we need a generic set of beams into which we can insert individual ping data.  Thhis will be the angular respnse curve
	# 	beamdetail = [0,0,0,0]
	# 	startAngle = -90
	# 	# make an arc which supports triple frequency.  we can then analyse all frequencies at the same time
	# 	ARC = [[pygsf.cBeam(beamdetail, i), pygsf.cBeam(beamdetail, i), pygsf.cBeam(beamdetail, i)] for i in range(startAngle, -startAngle)]
	# 	# use a dictionary so we can easily find the correct array by frequency
	# 	beamPointingAngles = []
	# 	transmitSector = []

	for filename in matches:
		if dump:
			dumpfile(filename, str(args.odir))

		if writeConditionedFile:
			createsubsetfile(filename, str(args.odir), exclude)
		# if extractBackscatter:
		# 	outFileName = os.path.join(os.path.dirname(os.path.abspath(matches[0])), args.odir, "AngularResponseCurve_.csv")
		# 	outFileName = createOutputFileName(outFileName)
		# 	ARC = extractARC(filename, ARC, pygsf.ARCIdx, beamPointingAngles, transmitSector)
		# 	# ARC, beamPointingAngles, transmitSector = extractARC(filename, ARC, ARCIdx, beamPointingAngles, transmitSector)

		update_progress("Processed: %s (%d/%d)" % (filename, fileCounter, len(matches)), (fileCounter/len(matches)))
		fileCounter +=1

	if extractBackscatter:
		saveARC(outFileName, ARC)

		update_progress("Process Complete: ", (fileCounter/len(matches)))

###############################################################################
def saveARC(outFileName, ARC):
	'''print out the extracted backscatter angular response curve'''
	print("Writing backscatter angular response curve to: %s" % outFileName)
	# compute the mean response across the swath
	responseSum = 0
	responseCount = 0
	responseAverage = 0
	# for record in ARC:
	# 	for each beam in record:
	# 		if beam.numberOfSamplesPerBeam > 0:
	# 			responseSum = responseSum = (beam.sampleSum/10) #tenths of a dB
	# 			responseCount = responseCount = beam.numberOfSamplesPerBeam
	# 	responseAverage = responseSum/responseCount
	with open(outFileName, 'w') as f:
		# write out the backscatter response curve
		f.write("TakeOffAngle(Deg),Sector,100kHz_ARC(dB),100kHzSampleSum,100kHzSampleCount,200kHz_ARC(dB),200kHzSampleSum,200kHzSampleCount,400kHz_ARC(dB),400kHzSampleSum,400kHzSampleCount,Correction\n")
		for record in ARC:
			for beam in record:
				if beam.numberOfSamplesPerBeam > 0:
					beam.samples.append (beam.sampleSum/beam.numberOfSamplesPerBeam)
				else:
					beam.samples.append (0)

			f.write("%.3f, %d, %.3f, %d, %d, %.3f, %d, %d, %.3f, %d, %d, %.3f\n" % (record[0].takeOffAngle, record[0].sector, record[0].samples[0], record[0].sampleSum, record[0].numberOfSamplesPerBeam, record[1].samples[0], record[1].sampleSum, record[1].numberOfSamplesPerBeam,record[2].samples[0], record[2].sampleSum, record[2].numberOfSamplesPerBeam, responseAverage))

###############################################################################
def	dumpfile(filename, odir):
	# create an output file based on the input
	outFileName = os.path.splitext(filename)[0]+'.txt'
	# outFileName = os.path.join(os.path.dirname(os.path.abspath(filename)), odir, os.path.splitext(os.path.basename(filename))[0] + "_subset" + os.path.splitext(os.path.basename(filename))[1])
	outFileName  = createOutputFileName(outFileName)
	outFilePtr = open(outFileName, 'w')
	print ("writing dump to file: %s" % outFileName)

	r = pygsf.GSFREADER(filename)
	counter = 0

	outFilePtr.write ("PingNumber, Latitude(Deg), Longitude(Deg), Frequency(Hz), SerialNumber, Heading(Deg), DepthCorrector(m), GPSTideCorrector(m), TideCorrector(m) \n")
	while r.moreData():
		# read a datagram.  If we support it, return the datagram type and aclass for that datagram
		numberofbytes, recordidentifier, datagram = r.readDatagram()
		# read the bytes into a buffer 
		rawBytes = r.readDatagramBytes(datagram.offset, numberofbytes)
		# the user has opted to skip this datagram, so continue
		if recordidentifier == pygsf.SWATH_BATHYMETRY:
			datagram.read()
			outFilePtr.write ("%d, %s, %.8f, %.8f, %d, %s, %.3f, %.3f, %.3f, %.3f\n" % (datagram.pingnumber, datagram.currentRecordDateTime(), datagram.latitude, datagram.longitude, datagram.frequency, datagram.serialnumber, datagram.heading, datagram.depthcorrector, datagram.gpstidecorrector, datagram.tidecorrector))
	
	outFilePtr.close()
	r.close()
	print ("Saving dump to: %s" % outFileName)		
	outFilePtr.close()
	return

###############################################################################
def	createsubsetfile(filename, odir, exclude):
	# create an output file based on the input
	outFileName = os.path.join(os.path.dirname(os.path.abspath(filename)), odir, os.path.splitext(os.path.basename(filename))[0] + "_subset" + os.path.splitext(os.path.basename(filename))[1])
	outFileName  = createOutputFileName(outFileName)
	outFilePtr = open(outFileName, 'wb')
	print ("writing subset to file: %s" % outFileName)

	r = pygsf.GSFREADER(filename)
	counter = 0

	while r.moreData():
		# read a datagram.  If we support it, return the datagram type and aclass for that datagram
		numberofbytes, recordidentifier, datagram = r.readDatagram()
		# read the bytes into a buffer 
		rawBytes = r.readDatagramBytes(datagram.offset, numberofbytes)
		# the user has opted to skip this datagram, so continue
		if recordidentifier in exclude:
			continue
		outFilePtr.write(rawBytes)
	r.close()
	print ("Saving conditioned file to: %s" % outFileName)		
	outFilePtr.close()
	return

# ###############################################################################
# def extractARC(filename, ARC, ARCIdx, beamPointingAngles, transmitSector):
# 	r = pygsf.GSFREADER(filename, True)

# 	while r.moreData():
# 		# read a datagram.  If we support it, return the datagram type and a class for that datagram
# 		numberofbytes, recordidentifier, datagram = r.readDatagram()

# 		'''to extract backscatter angular response curve we need to keep a count and sum of gsf samples in a per degree sector'''
# 		'''to do this, we need to take into account the take off angle of each beam'''
# 		if recordidentifier == pygsf.SWATH_BATHYMETRY:
# 			datagram.scalefactors = r.scalefactors
# 			datagram.perbeam = True
# 			datagram.snippettype = pygsf.SNIPPET_NONE  #define the snippet algorithm here.
# 			datagram.read()

# 			# we have an R2 system, so we can apply a backscatter correction algorithm
# 			samplearray = datagram.R2Soniccorrection()
# 			idx = pygsf.ARCIdx[datagram.frequency]
# 			for i in range(datagram.numbeams):
# 				# now place the results into the correct bucket based on frequency
# 				arcIndex = round(datagram.BEAM_ANGLE_ARRAY[i]- ARC[0][idx].takeOffAngle) # efficiently find the correct slot for the data
# 				ARC[arcIndex][idx].sampleMin = min(samplearray[i])
# 				ARC[arcIndex][idx].sampleMax = max(samplearray[i])
# 				ARC[arcIndex][idx].sampleSum += samplearray[i]
# 				ARC[arcIndex][idx].numberOfSamplesPerBeam += 1
# 				ARC[arcIndex][idx].sector = datagram.SECTOR_NUMBER_ARRAY[i]
# 	return ARC

###############################################################################
def from_timestamp(unixtime):
	return datetime(1970, 1 ,1) + timedelta(seconds=unixtime)

###############################################################################
def decdeg2dms(dd):
   is_positive = dd >= 0
   dd = abs(dd)
   minutes,seconds = divmod(dd*3600,60)
   degrees,minutes = divmod(minutes,60)
   degrees = degrees if is_positive else -degrees
   return (degrees,minutes,seconds)
###############################################################################
def update_progress(job_title, progress):
	length = 20 # modify this to change the length
	block = int(round(length*progress))
	msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
	if progress >= 1: msg += " DONE\r\n"
	sys.stdout.write(msg)
	sys.stdout.flush()

###############################################################################
def createOutputFileName(path):
	'''Create a valid output filename. if the name of the file already exists the file name is auto-incremented.'''
	path	  = os.path.expanduser(path)

	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	if not os.path.exists(path):
		return path

	root, ext = os.path.splitext(os.path.expanduser(path))
	dir	   = os.path.dirname(root)
	fname	 = os.path.basename(root)
	candidate = fname+ext
	index	 = 1
	ls		= set(os.listdir(dir))
	while candidate in ls:
			candidate = "{}_{}{}".format(fname,index,ext)
			index	+= 1

	return os.path.join(dir, candidate)

###############################################################################
if __name__ == "__main__":
	start_time = time.time() # time  the process
	main()
	print("Duration: %d seconds" % (time.time() - start_time))
