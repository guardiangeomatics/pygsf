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

```
def readfile(filename):
	reader = GSFREADER(filename) # create a GSFREADER class and pass the filename
	print ("Read the file...")
	while reader.moreData():
		numberofbytes, recordidentifier, datagram = reader.readDatagram()
		print(reader.recordnames[recordidentifier])
	return
```



