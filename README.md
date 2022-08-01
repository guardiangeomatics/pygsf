# PYGSF 
## Native python reader for generic sensor format (gsf) files.

## Introduction

As the industry moves towards cloud computing, remote processing and multi CPU processing using an open stack codebase, Guardian Geomatics has taken the path of opening some of our sources for student, government and researches to use free of charge.

This is a native pure python reader of the Generic Sensor Format (GSF) binary file format.  While the file format is relatively complex, it has the following benefits over other widely used file formats.

* Durable
The file format has been around for many years.  It was designed and built by Leidos https://www.leidos.com/products/ocean-marine for the US Department of Defense to efficiently store and exchange geophysical data before processing into either vector or raster form. The structure is particularly useful for data sets created by systems such as multibeam echosounders that collect a large quantity of data. GSF is designed to be modular and adaptable to meet the unique requirements of a variety of sensors.

* Self Contained
The file is well structured with strong typing, arrays, structures.  It does not require additional files for the data to be analysed or procesed.

* Efficient
The file format is extremely space efficient. This comes about from an excellent design of repackaging data into integer formats, strict adherence to not wasting space at any time, even if it appears a religious experience. 

* Portable
By being space efficient, the files are MUCH smaller than the same data in vendor specific file formats.  This means the open and read, write faster both locally and across the network.

* Compressible
The design used integer arrays to store geophysical data.  This would appear to be a little dated given terabytes of storage are now cheap, but please consider this example.

| File | Bytes | % Size |
| ------------------- | ------------------------ | ---------------------- |
| IDN-JI-SR23_1-PH-B46-001_0005_20220419_171703.KMALL |1,362,533,000 | 100%|
| Same data in GSF file| 207,574,000 | 15.2%|
| Same data in GSF.7Z | 58,742,000| 4.3%|

The file reduction is impressive.  It is worth noting that we have NOT reduced the number of position, attitude, soundings, backscatter observations in the file.  We have removed the items processing packages typically ignore at import stage.  additionally we have restructured the data into a computationally efficient structure.

Overall, GSF is excellent.  where it has struggled is the file format is SO dense, it is not easy to read.  There is a very good C library (gsflib) which is great if you are a seasoned programmer.  If you are a student, researcher or keen data processor who wish to access the GSF files, then they were pretty impregnable.
The folks at Guardian Geomatics recognise that remote processing, cloud processing and massive parallel processing are now on our doorsteps and we need to leverage this technologies.  To assist the industry in this regards, we have decided to release pygsf.
Pygsf will efficiently parse a GSF file for the various components you need to pull into a python script.  This can be a simple python list for making a track plot, understanding data holdings, coverage or a numpy array for more complex tasks.

## Sample Reader
The GSF reader removes the complexity of the file format.  All you need to do is open the file and then read in a loop until all the datagrams in the file are read and we are at end of file.

```
def readfile(filename):
	reader = GSFREADER(filename) # create a GSFREADER class and pass the filename
	while reader.moreData():
		numberofbytes, recordidentifier, datagram = reader.readdatagram()
		print(reader.recordnames[recordidentifier])
	return
```

which will print the name of each datagram.....

```
SWATH_BATHYMETRY
SWATH_BATHYMETRY
ATTITUDE
SWATH_BATHYMETRY
SWATH_BATHYMETRY
SWATH_BATHYMETRY
```

You will typically need to dig into the datagram to access the contents.  this is accomplished by calling datagram.read(), which will decode each record type and present them back to you in native python objects, lists, numpy arrays as appopriate for the data type in question

```
	reader = GSFREADER(filename) # create a GSFREADER class and pass the filename
	while reader.moreData():
		numberofbytes, recordidentifier, datagram = reader.readdatagram()
		if recordidentifier == SWATH_BATHYMETRY:
			datagram.read()
			print (datagram.timestamp, datagram.longitude, datagram.latitude)

```

Digging a little deeper you, when reading the SWATH_BATHYMETRY records you can easily load these into a numpy array as follows:

```
	reader = GSFREADER(filename) # create a GSFREADER class and pass the filename
	while reader.moreData():
		numberofbytes, recordidentifier, datagram = reader.readdatagram()
		print(reader.recordnames[recordidentifier])

		if recordidentifier == SWATH_BATHYMETRY:
			reader.scalefactorsd = datagram.read()
			depths = datagram.DEPTH_ARRAY
			print (depths)

```

which will print the depth array of the ping.....

```
[25.575 25.564 25.556 25.524 25.548 25.608 25.613 25.598 25.605 25.575
 25.576 25.638 25.609 25.611 25.588 25.603 25.561 25.582 25.582 25.589
 25.595 25.607 25.597 25.581 25.583 25.557 25.62  25.62  25.619 25.619
 25.612 25.602 25.599 25.511 25.639 25.633 25.623 25.62  25.578 25.675
 25.636 25.631 25.606 25.566 25.563 25.644 25.638 25.608 25.568 25.687
 25.609 25.612 25.597 25.579 25.588 25.594 25.615 25.605 25.6   25.561
 25.593 25.629 25.603 25.61  25.598 25.639 25.666 25.658 25.668 25.622
 25.657 25.645 25.639 25.607 25.62  25.657 25.686 25.659 25.632 25.61
 25.586 25.563 25.552 25.53  25.519 25.516 25.552 25.585 25.577 25.576
 25.556 25.569 25.57  25.567 25.739 25.683 25.713 25.675 25.635 25.633
 25.622 25.623 25.61  25.586 25.592 25.597 25.628 25.649 25.655 25.631
 25.604 25.637 25.698 25.691 25.659 25.662 25.667 25.641 25.637 25.575
 25.609 25.605 25.512 25.556 25.567 25.53  25.569 25.654 25.583 25.603
 25.63  25.635 25.646 25.663 25.671 25.632 25.665 25.669 25.609 25.612
 25.595 25.536 25.521 25.513 25.533 25.534 25.526 25.649 25.621 25.624
 25.636 25.653 25.722 25.701 25.664 25.618 25.595 25.541 25.593 25.578
 25.563 25.577]
```

There are many record types to decode depending on your requirement.  The most common used sets of data are within the SWATH_BATHYMETRY array.  When pygsf reads these files it passes them back to your program as numpy arrays.  the following arrays are available...

```
DEPTH_ARRAY							=	1
ACROSS_TRACK_ARRAY					=	2
ALONG_TRACK_ARRAY					=	3
TRAVEL_TIME_ARRAY					=	4
BEAM_ANGLE_ARRAY					=	5
MEAN_CAL_AMPLITUDE_ARRAY			=	6
MEAN_REL_AMPLITUDE_ARRAY			=	7
ECHO_WIDTH_ARRAY					=	8
QUALITY_FACTOR_ARRAY				=	9
RECEIVE_HEAVE_ARRAY					=	10
DEPTH_ERROR_ARRAY					=	11
ACROSS_TRACK_ERROR_ARRAY			=  	12
ALONG_TRACK_ERROR_ARRAY				=	13
NOMINAL_DEPTH_ARRAY					=	14
QUALITY_FLAGS_ARRAY					=	15
BEAM_FLAGS_ARRAY					=	16
SIGNAL_TO_NOISE_ARRAY				=	17
BEAM_ANGLE_FORWARD_ARRAY			=	18
VERTICAL_ERROR_ARRAY				=	19
HORIZONTAL_ERROR_ARRAY				=	20
INTENSITY_SERIES_ARRAY				=	21
SECTOR_NUMBER_ARRAY					=	22
DETECTION_INFO_ARRAY				=	23
INCIDENT_BEAM_ADJ_ARRAY				=	24
SYSTEM_CLEANING_ARRAY				=	25
DOPPLER_CORRECTION_ARRAY			=	26
SONAR_VERT_UNCERTAINTY_ARRAY		=	27
SCALE_FACTORS						=	100

```
