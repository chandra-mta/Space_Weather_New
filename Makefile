# -*- makefile -*-
#####################################################################
#																	#
# 	Make file for Space Weather/Radiation related Sites				#
# 																	#
# 		author: t isobe (tisobe@cfa.harvard.edu)					#
# 		last update: Mar 26, 2020									#
# 																	#
#####################################################################

#
#--- Change the following lines to appropriate ones
#
#   	TASK: 	 task name;  the script will be kept there
#   	NROOT: 	 main script directory
#   	NHTML:   main web directory
#		NADDRESS: web address
#
#   	OROOT: 	 saved main script directory
#   	OHTML:   saved main web directory
#   	SHTML:   saved main web directory -- directory where web pages are saved with scripts
#		OADDRESS: web address
#
TASK	 = Space_Weather
VERSION  = 1.0
NROOT	= /data/mta/Script
NMAIN	= $(NROOT)/$(TASK)
NHTML	= /data/mta_www/MIRROR/Space_Weather
NADDRESS = cxc.cfa.harvard.edu
#
#--- changing lines in scripts (they will be replaced by the lines defined above)
#
OROOT	= /data/mta4
OMAIN	= $(OROOT)/Space_Weather
OHTML	= /data/mta4/www/RADIATION_new
SHTML	= /data/mta4/Space_Weather/Web_dir
OADDRESS = cxc.cfa.harvard.edu
#
#--- Define lists of sub directories
#
M_LIST = ACE ACIS_Rad ALERTS Comm_data CRM3 EPHEM GOES GSM_plots KP MTA_Rad SOHO STEREO TLE XMM
N_LIST = house_keeping Doc

install:
	for SITE  in $(M_LIST); do \
		echo  $(NMAIN)/$${SITE}/Scripts;\
		mkdir -p $(NMAIN)/$${SITE}/Scripts;\
		mkdir -p $(NMAIN)/$${SITE}/Data;\
		rsync -r --times --cvs-exclude $${SITE}/Scripts/* ${NMAIN}/$${SITE}/Scripts/;\
	done
	
	for ENT in $(wildcard $(NMAIN)/*/Scripts/*); do \
		sed -i "s,$(OMAIN),$(NMAIN),g" $$ENT;\
		sed -i "s,$(OHTML),$(NHTML),g"			$$ENT;\
		sed -i "s,$(OMAIN),$(NMAIN),g"			$$ENT;\
		sed -i "s,$(OROOT),$(NROOT),g"			$$ENT;\
	done   

	for ENT in $(wildcard $(NMAIN)/*/Scripts/Template/*); do \
		sed -i "s,$(OADDRESS),$(NADDRESS),g"	$$ENT;\
		sed -i "s,$(OHTML),$(NHTML),g"			$$ENT;\
		sed -i "s,$(OMAIN),$(NMAIN),g"			$$ENT;\
		sed -i "s,$(OROOT),$(NROOT),g"			$$ENT;\
	done   

	for SITE in $(N_LIST); do \
		echo  $(NMAIN)/$${SITE};\
		mkdir -p $(NMAIN)/$${SITE};\
		rsync -r --times --cvs-exclude $${SITE}/* ${NMAIN}/$${SITE};\
	done

	for ENT in $(wildcard $(NMAIN)/house_keeping/* $(NMAIN)/CRMFLX/* $(NMAIN)/geopack/*); do \
		sed -i "s,$(OADDRESS),$(NADDRESS),g"	$$ENT;\
		sed -i "s,$(OHTML),$(NHTML),g"			$$ENT;\
		sed -i "s,$(OMAIN),$(NMAIN),g"			$$ENT;\
		sed -i "s,$(OROOT),$(NROOT),g"			$$ENT;\
	done
	gfortran -std=legacy -ffixed-form -fd-lines-as-comments -ffixed-line-length-none $(NMAIN)/CRM3/Scripts/runcrm.f $(NMAIN)/CRMFLX/CRMFLX_V33/CRMFLX_V33.f -o $(NMAIN)/CRM3/Scripts/runcrm
#
#--- copying html pages
#
ifdef NHTML
	mkdir -p $(NHTML)
	rsync  -r --times --cvs-exclude $(OMAIN)/Web_dir/* $(NHTML)
endif
#
#--- Create a distribution tar file for this program
#
dist:
	mkdir $(TASK)-$(VERSION)
	rsync -aruvz --cvs-exclude --exclude $(TASK)-$(VERSION) * $(TASK)-$(VERSION)
	tar cvf $(TASK)-$(VERSION).tar $(TASK)-$(VERSION)
	gzip --best $(TASK)-$(VERSION).tar
	rm -rf $(TASK)-$(VERSION)/

