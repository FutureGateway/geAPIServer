#!/bin/sh 
#
# myRepast-infection - portlet pilot script
#
# The following script does:
#   o Perform a simulation using the provided parameters
#   o Create a archive containinG the output file.  
# 
# Author: mario.torrisi@ct.infn.it
#

SW_NAME="repast" # Software name 

echo "--------------------------------------------------"
echo "Job execution starts on: '"$(date)"'"

echo "---[HOME directory]-------------------------------"
ls -l $HOME

echo "---[Working directory]-------------------------"
mkdir output
ls -l $(pwd)

/bin/bash $HOME/$SW_NAME/simulation.sh $1 $2 $3 $4 > stdout

#
# Following statement produce the simulation_output file
#
OUTFILE=simulation_output.txt
echo "--------------------------------------------------"  > $OUTFILE
echo "Simulation started at: '"$(date)"'"                 >> $OUTFILE
echo ""                                                   >> $OUTFILE
echo "#################[  START LOG  ]##################" >> $OUTFILE
echo ""                                                   >> $OUTFILE
cat stdout                                                >> $OUTFILE
echo "#################[   END LOG   ]##################" >> $OUTFILE
echo ""                                                   >> $OUTFILE
echo "Simulation ended at: '"$(date)"'"                   >> $OUTFILE
echo "--------------------------------------------------" >> $OUTFILE
echo ""                                                   >> $OUTFILE

#
# Collect all generated output files into a single tar.gz file
#
tar cvfz myRepast-infection-Files.tar.gz $OUTFILE output/

echo "Done!"

