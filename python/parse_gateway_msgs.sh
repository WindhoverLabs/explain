#!/bin/bash

#-------------
# Variables to set
#-------------
#Path to source binary compiled with -g flag
PATH_TO_SRC_EXE="/home/vagrant/Desktop/OSR/gateway/sims/SIM_aug_module/S_main_Linux_5.4_x86_64.exe"
#Path to destination binary compiled with -g flag
PATH_TO_DST_EXE="/home/vagrant/Desktop/OSR/gateway/sims/SIM_aug_module/S_main_Linux_5.4_x86_64.exe"
#Input message symbol names this assumes the names are the same in src and dst
INPUT_MSG_ARRAY=("StarTrackerTelemetry" "ImuTelemetry" "LidarTelemetry" "SbandSensorTelemetry" "VisibleNfovCameraTelemetry")
#Output message symbol names also assumes names are the same in src and dst binaries
OUTPUT_MSG_ARRAY=("DveFireCommand" "RcsFireCommand")
#Combined output file name
OUTPUT_FILE_NAME="explain_output.json"
#Combined input file name
INPUT_FILE_NAME="explain_input.json"
#Merged file name output of jsoncombine.py
MERGED_FILE_NAME="merged_file.json"

# No editing should be needed beyond this point.

#-------------
# Get Telemetry Message Memory Maps
#-------------
for i in ${INPUT_MSG_ARRAY[@]}
do
echo "Parsing input $i memory map"
python pyexplain.py -o "$i" -m 0 -ss "$i" -ds "$i" -sf $PATH_TO_SRC_EXE -df $PATH_TO_DST_EXE
done

# Merge json files 
echo "Merging input files ${INPUT_MSG_ARRAY[*]}"
python jsoncombine.py ${INPUT_MSG_ARRAY[*]}

# Rename merged_file.json
echo "Renaming $MERGED_FILE_NAME to $INPUT_FILE_NAME"
mv $MERGED_FILE_NAME $INPUT_FILE_NAME

#-------------
# Get Command Message Memory Maps 
#-------------
for i in ${OUTPUT_MSG_ARRAY[@]}
do
echo "Parsing output $i memory map"
python pyexplain.py -o "$i" -m 0 -ss "$i" -ds "$i" -sf $PATH_TO_SRC_EXE -df $PATH_TO_DST_EXE
done

# Merge json files 
echo "Merging input files ${OUTPUT_MSG_ARRAY[*]}"
python jsoncombine.py ${OUTPUT_MSG_ARRAY[*]}

# Rename merged_file.json
echo "Renaming $MERGED_FILE_NAME to $OUTPUT_FILE_NAME"
mv $MERGED_FILE_NAME $OUTPUT_FILE_NAME

#-------------
# Cleanup
#-------------
echo "cleanup"
for i in ${INPUT_MSG_ARRAY[@]}
do
echo "removing $i"
rm "$i"
done

for i in ${OUTPUT_MSG_ARRAY[@]}
do
echo "removing $i"
rm "$i"
done

