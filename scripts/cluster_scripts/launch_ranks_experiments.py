import subprocess
from utils.UpdateParameter import *



parameter_file = "experiments/nipes/parameters.csv"

parameter_text = """
#experimentName,string,nipes
#subexperimentName,string,measure_ranks
#preTextInResultFile,string,ftest5
#resultFile,string,result5.txt


#expPluginName,string,/usr/local/lib/libNIPES.so
#scenePath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/experiments/sim/obstacles_2.ttt
#robotPath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/experiments/sim/model0.ttm
#modelPath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/experiments/sim/

#repository,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/logs
#fitnessFile,string,fitnesses.csv
#evalTimeFile,string,eval_durations.csv
#behavDescFile,string,final_pos.csv
#stopCritFile,string,stop_crit.csv
#noveltyFile,string,novelty.csv
#archiveFile,string,archive.csv
#energyCostFile,string,energyCost.csv
#simTimeFile,string,simTime.csv

#isScreenshotEnable,bool,0
#isVideoRecordingEnable,bool,0

#jointControllerType,int,0
#verbose,bool,1
#instanceType,int,0
#killWhenNotConnected,bool,0
#shouldReopenConnections,bool,0
#seed,int,7

#populationSize,int,80
#maxEvalTime,float,30.0
#maxNbrEval,int,10000
#timeStep,float,0.1

#modifyMaxEvalTime,bool,0
#constantmodifyMaxEvalTime,float,0.0
#minEvalTime,float,2.0

#noiseLevel,double,0.
#maxVelocity,double,10.

#envType,int,1
#arenaSize,double,2.
#target_x,double,0.75
#target_y,double,0.75
#target_z,double,0.05
#init_x,float,0
#init_y,float,0
#init_z,float,0.05
#MaxWeight,float,1.0
#energyBudget,double,100
#energyReduction,bool,0
#NNType,int,2
#NbrInputNeurones,int,8
#NbrOutputNeurones,int,2
#NbrHiddenNeurones,int,8
#UseInternalBias,bool,1

#reloadController,bool,1
#CMAESStep,double,1.
#FTarget,double,0.05
#elitistRestart,bool,0
#withRestart,bool,1
#incrPop,bool,0
#lengthOfStagnation,int,20
#kValue,int,15
#noveltyThreshold,double,0.9
#archiveAddingProb,double,0.4
#noveltyRatio,double,1.
#noveltyDecrement,double,0.05
#populationStagnationThreshold,float,0.01

#nbrWaypoints,int,50
#withBeacon,bool,1
#flatFloor,bool,1
#use_sim_sensor_data,bool,0
#withTiles,bool,1     

"""

mass_update_parameters(parameter_file, parameter_text)


exec_res=subprocess.run(f"bash launch.sh -e=nipes",shell=True, capture_output=True)  



"sbatch --job-name=mnar --cpus-per-task=32 are-parallel.job experiment_name starting_port number_of_simulator"