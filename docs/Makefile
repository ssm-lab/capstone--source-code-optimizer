# Makefile
# TODO: Missing artifacts should be added to this file
.PHONY:	SRS

all:	SRS MG MIS PS VnVP VnVR DevP HazA Refl UseTest clean

SRS:
	cd SRS && make && cd -

MG:
	cd Design/SoftArchitecture && make && cd -

MIS:
	cd Design/SoftDetailedDes && make && cd -

PS:
	cd ProblemStatementAndGoals && make && cd -

VnVP:
	cd VnVPlan && make && cd -

VnVR:
	cd VnVReport && make && cd -
	
DevP:
	cd DevelopmentPlan && make && cd -
	
HazA:
	cd HazardAnalysis && make && cd -
	
Refl:
	cd ReflectAndTrace && make && cd -
	
UseTest:
	cd Extras/UsabilityTesting && make && cd -

UseMan:
	cd Extras/UserManual && make && cd -

clean:	cleanSRS cleanMG cleanMIS cleanPS cleanVnVP cleanVnVR cleanDevP cleanHazA cleanRefl cleanUseTest

cleanPS:
	cd ProblemStatementAndGoals && make clean && cd -

cleanSRS:
	cd SRS && make clean && cd -

cleanMG:
	cd Design/SoftArchitecture && make clean && cd -

cleanMIS:
	cd Design/SoftDetailedDes && make clean && cd -

cleanVnVP:
	cd VnVPlan && make clean && cd -

cleanVnVR:
	cd VnVReport && make clean && cd -
	
cleanDevP:
	cd DevelopmentPlan && make clean && cd -
	
cleanHazA:
	cd HazardAnalysis && make clean && cd -
	
cleanRefl:
	cd ReflectAndTrace && make clean && cd -
	
cleanUseTest:
	cd Extras/UsabilityTesting && make clean && cd -

cleanUseMan:
	cd Extras/UserManual && make clean && cd -
