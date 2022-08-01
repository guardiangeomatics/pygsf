# the rejection flags used by this software
REJECT_CLIP = -1
REJECT_RANGE= -2
REJECT_INTENSITY= -4

###############################################################################
def clippolar(datagram, leftclipdegrees, rightclipdegrees):
	'''sets the processing flags to rejected if the beam angle is beyond the clip parameters'''
	if datagram.numbeams == 0:
		return
	if len(datagram.QUALITY_FACTOR_ARRAY) != len(datagram.TRAVEL_TIME_ARRAY):
		return
	for i, s in enumerate(datagram.BEAM_ANGLE_ARRAY):
		if (s <= leftclipdegrees) or (s >= rightclipdegrees):
			datagram.QUALITY_FACTOR_ARRAY[i] += REJECT_CLIP
			# datagram.MEAN_REL_AMPLITUDE_ARRAY[i] = 0
			# datagram.ACROSS_TRACK_ARRAY[i] = 0
	return

###############################################################################
def cliptwtt(datagram, minimumtraveltime=0.0):
	'''sets the processing flags to rejected if the two way travel time is less than the clip parameters'''
	if datagram.numbeams == 0:
		return
	if len(datagram.QUALITY_FACTOR_ARRAY) != len(datagram.TRAVEL_TIME_ARRAY):
		return
	for i, s in enumerate(datagram.TRAVEL_TIME_ARRAY):
		if (s <= minimumtraveltime):
			datagram.QUALITY_FACTOR_ARRAY[i] += REJECT_RANGE
	return

###############################################################################
def clipintensity(datagram, minimumintenisty=0.0):
	'''sets the processing flags to rejected if the two way travel time is less than the clip parameters'''
	if datagram.numbeams == 0:
		return
	if len(datagram.QUALITY_FACTOR_ARRAY) != len(datagram.TRAVEL_TIME_ARRAY):
		return
	for i, s in enumerate(datagram.MEAN_REL_AMPLITUDE_ARRAY):
		if (s <= minimumintenisty):
			datagram.QUALITY_FACTOR_ARRAY[i] += REJECT_INTENSITY
	return


	###############################################################################
	def backscatteradjustment(self, S1_angle, S1_twtt, S1_range, S1_Magnitude, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset):
		'''R2Sonic backscatter correction algorithm from Norm Camblell at CSIRO.  This is a port from F77 fortran code, and has been tested and confirmed to provide identical results'''
		# the following code uses the names for the various packets as listed in the R2Sonic SONIC 2024 Operation Manual v6.0
		# so names beginning with
		# H0_   denote parameters from the BATHY (BTH) and Snippet (SNI) packets from section H0
		# R0_   denote parameters from the BATHY (BTH) packets from section R0
		# S1_   denote parameters from the Snippet (SNI) packets from section S1
		# names beginning with
		# z_	denote values derived from the packet parameters
		# the range, z_range_m, can be found from the two-way travel time (and scaling factor), and the sound speed, as follows:

		one_rad = 57.29577951308232
		S1_angle_rad = S1_angle / one_rad
		z_one_way_travel_secs = S1_twtt / 2.0
		z_range_m = z_one_way_travel_secs * H0_SoundSpeed

		# there is a range of zero, so this is an invalid beam, so quit
		if z_range_m == 0:
			return 0

		###### TRANSMISSION LOSS CORRECTION ##########################################
		# according to Lurton, Augustin and Le Bouffant (Femme 2011), the basic Sonar equation is
		# received_level = source_level - 2 * transmission_loss + target_strength + receiver_gain
		# note that this last term does not always appear explicitly in the sonar equation
		# more specifically:
		# transmission_loss = H0_RxAbsorption * range_m + 40 log10 ( range_m )
		# target_strength = backscatter_dB_m + 10 log10 ( z_area_of_insonification )
		# receiver_gain = TVG + H0_RxGain
		# the components of the Sonar equation can be calculated as follows:
		# u16 S1_Magnitude[S1_Samples]; // [micropascals] = S1_Magnitude[n]

		z_received_level = 20.0 * math.log10 ( S1_Magnitude )
		z_source_level = H0_TxPower # [dB re 1 uPa at 1 meter]
		z_transmission_loss_t1 = 2.0 * H0_RxAbsorption * z_range_m / 1000.0  # [dB per kilometer]
		z_transmission_loss_t2 = 40.0 * math.log10(z_range_m)
		z_transmission_loss = z_transmission_loss_t1 + z_transmission_loss_t2
	
		###### INSONIFICATION AREA CORRECTION Checked 19 August 2017 p.kennedy@fugr.com ##########################################	
		# for oblique angles
			# area_of_insonification = along_track_beam_width * range * sound_speed * pulse_width / 2 sin ( incidence_angle)
		# for normal incidence
			# area_of_insonification = along_track_beam_width * across_track_beam_width * range ** 2

		sin_S1_angle = math.sin ( abs ( S1_angle_rad ) )

		# from Hammerstad 00 EM Technical Note Backscattering and Seabed Image Reflectivity.pdf
		# A = ψTψr*R^2 around normal incidence
		z_area_of_insonification_nml = H0_TxBeamWidthVert * H0_TxBeamWidthHoriz * z_range_m **2 

		# A = ½cτ ψTR/sinφ elsewhere
		if ( abs ( S1_angle ) >= 0.001 ):
			z_area_of_insonification_obl = 0.5 * H0_SoundSpeed * H0_TxPulseWidth * H0_TxBeamWidthVert * z_range_m / sin_S1_angle

		if ( abs ( S1_angle ) < 25. ):
			z_area_of_insonification = z_area_of_insonification_nml
		else:
			z_area_of_insonification = z_area_of_insonification_obl

		if ( abs ( S1_angle ) < 0.001 ):
			z_area_of_insonification = z_area_of_insonification_nml
		elif ( z_area_of_insonification_nml < z_area_of_insonification_obl ):
			z_area_of_insonification = z_area_of_insonification_nml
		else:
			z_area_of_insonification = z_area_of_insonification_obl

		###### TIME VARIED GAIN CORRECTION  19 August 2017 p.kennedy ##########################################
		# note that the first equation refers to the along-track beam width
		# the R2Sonic Operation Manual refers on p21 to the Beamwidth - Along Track -- moreover, for the 2024, the Beamwidth Along Track is twice
		# the Beamwidth Across Track

		# according to the R2Sonic Operation Manual in Section 5.6.3 on p88, the TVG equation is:
		# TVG = 2*R* α/1000 + Sp*log(R) + G
		# where:
		# α = Absorption Loss db/km			(H0_RxAbsorption)
		# R = Range in metres				(range_m)
		# Sp = Spreading loss coefficient	(H0_RxSpreading)
		# G = Gain from Sonar Control setting (H0_RxGain)

		TVG_1 = 2.0 * z_range_m * H0_RxAbsorption / 1000.
		TVG_2 = H0_RxSpreading * math.log10 ( z_range_m )		
		TVG = TVG_1 + TVG_2 + H0_RxGain

		# as per email from Beaudoin, clip the TVG between 4 and 83 dB
		TVG = min(max(4, TVG ), 83)

		###### NOW COMPUTE THE CORRECTED BACKSCATTER ##########################################
		backscatter_dB_m = z_received_level - z_source_level + z_transmission_loss - (10.0 * math.log10 ( z_area_of_insonification )) - TVG - H0_VTX_Offset + 100.0

		return backscatter_dB_m



	# def testR2SonicAdjustment():
# 	'''
# 	This test code confirms the results are in alignment with those from Norm Campbell at CSIRO who kindly provided the code in F77
# 	'''
# 	# adjusted backscatter		  -38.6
# 	# adjusted backscatter		  -47.6
# 	# adjusted backscatter		  -27.5
# 	# adjusted backscatter		  -36.6
# 	# adjusted backscatter		  -35.5

# 	S1_angle = -58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 197.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 35.0
# 	H0_RxGain = 8.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10(S1_uPa)

# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)

# 	S1_angle = -58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 206.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 35.0
# 	H0_RxGain = 8.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10 ( S1_uPa )
# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)

# 	S1_angle = - 58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 197.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 30.0
# 	H0_RxGain = 8.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10 ( S1_uPa )
# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)

# 	S1_angle = - 58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 197.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 35.0
# 	H0_RxGain = 6.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10 ( S1_uPa )
# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)


# 	S1_angle = - 58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 207.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 30.0
# 	H0_RxGain = 6.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10 ( S1_uPa )
# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)

# 	return

###############################################################################
		# if recordidentifier == SWATH_BATHYMETRY:
		# 	datagram.read()
		# 	datagram.snippettype = SNIPPET_NONE
			# print ("%s Lat:%.3f Lon:%.3f Ping:%d Freq:%d Serial %s" % (datagram.currentRecordDateTime(), datagram.latitude, datagram.longitude, datagram.pingnumber, datagram.frequency, datagram.serialnumber))

			# for cross profile plotting
			# bs = []
			# for s in datagram.MEAN_REL_AMPLITUDE_ARRAY:
			# 	if s != 0:
			# 		bs.append(20 * math.log10(s) - 100)
			# 	else:
			# 		bs.append(0)

			# bs = [20 * math.log10(s) - 100 for s in datagram.MEAN_REL_AMPLITUDE_ARRAY]
			# samplearray = datagram.R2Soniccorrection()
			# if datagram.frequency == 100000:
			# 	freq100 = mean(samplearray)
			# if datagram.frequency == 200000:
			# 	freq200 = mean(samplearray)
			# if datagram.frequency == 400000:
			# 	freq400 = mean(samplearray)
			# 	# print ("%d,%d,%.3f,%.3f,%.3f" %(pingcount, datagram.pingnumber, freq100, freq200, freq400))
			# 	print ("%d" %(pingcount))
			# 	pingcount += 1
				# if len(bs) > 0:
				# 	plt.plot(datagram.BEAM_ANGLE_ARRAY, bs, linewidth=0.25, color='blue')
				# 	plt.ylim([-60,-5])
				# 	plt.xlim([-60,60])
				# 	# ax3.plot(datagram.BEAM_ANGLE_ARRAY, datagram.ALONG_TRACK_ARRAY)
				# 	plt.pause(0.001)

			# datagram.clippolar(-60, 60)
		# r.fileptr.seek(numberofbytes, 1) # set the file ptr to the end of the record			
							