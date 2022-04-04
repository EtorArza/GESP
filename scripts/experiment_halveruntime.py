from argparse import ArgumentError

from utils.UpdateParameter import *
import subprocess
import time
import re
from os.path import exists
import sys

seeds = list(range(2,12))
port = int(10e6)

savefig_paths = ["results/figures", "/home/paran/Dropbox/BCAM/07_estancia_1/paper/images"]


n_tasks = 3
task_list = ["ExploreObstacles", "ExploreObstaclesDistanceBonus", "ExploreHardRace"]
scene_list = ["shapes_exploration.ttt", "shapes_exploration_bounus_4_distance.ttt", "hard_race.ttt"]

for index, task, scene in zip(range(n_tasks), task_list, scene_list):


    if len(sys.argv) != 2:
        raise ArgumentError("this script requires only one argument --plot --launch_local or --launch_cluster")

    if sys.argv[1] not in ("--plot", "--launch_local", "--launch_cluster"):
        raise ArgumentError("this script requires only one argument --plot --launch_local or --launch_cluster")


    # update parameters
    if sys.argv[1] in ("--launch_local", "--launch_cluster"):
        parameter_file = "experiments/nipes/parameters.csv"
        parameter_text = f"""
#experimentName,string,nipes
#subexperimentName,string,halving
#preTextInResultFile,string,seed_2
#resultFile,string,../results/data/halveruntime_results/runtimereduced_result_2.txt


#expPluginName,string,/usr/local/lib/libNIPES.so
#scenePath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/simulation/models/scenes/{scene}
#robotPath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/simulation/models/robots/model0.ttm
#modelsPath,string,/home/paran/Dropbox/BCAM/07_estancia_1/code/evolutionary_robotics_framework/simulation/models

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
#seed,int,2

#populationSize,int,40
#maxEvalTime,float,30.0
#maxNbrEval,int,3000
#timeStep,float,0.1


#halveMaxEvalTime,bool,1
#minEvalTime,float,3.0

#noiseLevel,double,0.
#maxVelocity,double,10.

#envType,int,1
#arenaSize,double,2.
#target_x,double,0.75
#target_y,double,0.75
#target_z,double,0.05
#init_x,float,0
#init_y,float,0
#init_z,float,0.12
#initPosition,sequence_double,0;0;0.12
#evaluationOrder,int,1

#MaxWeight,float,1.0
#energyBudget,double,100
#energyReduction,bool,0
#NNType,int,2
#NbrInputNeurones,int,2
#NbrOutputNeurones,int,4
#NbrHiddenNeurones,int,8
#UseInternalBias,bool,1

#reloadController,bool,1
#CMAESStep,double,1.
#FTarget,double,-0.05
#elitistRestart,bool,0
#withRestart,bool,1
#incrPop,bool,0
#lengthOfStagnation,int,200
#kValue,int,15
#noveltyThreshold,double,0.9
#archiveAddingProb,double,0.4
#noveltyRatio,double,1.
#noveltyDecrement,double,0.05
#populationStagnationThreshold,float,0.00001

#nbrWaypoints,int,50
#withBeacon,bool,1
#flatFloor,bool,1
#use_sim_sensor_data,bool,0
#withTiles,bool,1     
#jointSubs,sequence_int,-1;-1;-1;0;1;2
"""

        mass_update_parameters(parameter_file, parameter_text)




    #region local_launch

    if sys.argv[1] == "--launch_local":
        import itertools
        import time


        def run_with_seed_and_runtime(seed):

            time.sleep(0.5)
            update_parameter(parameter_file, "seed", str(seed))
            update_parameter(parameter_file, "resultFile", f"../results/data/halveruntime_results/{task}_halveruntime_exp_result_{seed}.txt")
            update_parameter(parameter_file, "preTextInResultFile", f"seed_{seed}")
            print("Launching ARE in experiment_halveruntime.py ...")
            exec_res=subprocess.run(f"bash launch.sh --coppelia -e=nipes --parallel",shell=True, capture_output=True)
            with open(f"{task}_halveruntime_logs_{seed}.txt", "w") as f:
                f.write("------------------")
                f.write("OUT: ")
                f.write(exec_res.stdout.decode("utf-8"))
                f.write("ERR: ")
                f.write(exec_res.stderr.decode("utf-8"))
                f.write("------------------")
            
        for seed in seeds:
            run_with_seed_and_runtime(seed)


    #endregion


    #region launch_cluster

    if sys.argv[1] == "--launch_cluster":
        import itertools
        import time


        def run_with_seed_and_runtime(seed, port):

            time.sleep(0.5)
            update_parameter(parameter_file, "seed", str(seed))
            update_parameter(parameter_file, "resultFile", f"../results/data/halveruntime_results/{task}_halveruntime_exp_result_{seed}.txt")
            update_parameter(parameter_file, "preTextInResultFile", f"seed_{seed}")
            print("Launching ARE in experiment_halveruntime.py ...")
            # Parallel
            subprocess.run(f"bash launch.sh -e=nipes --vrep --cluster --parallel --port={port} > {task}_halveruntime_logs_{seed}.txt 2>&1",shell=True)

            # # Sequential
            # subprocess.run(f"bash launch.sh -e=nipes --cluster --port={port} --sequential",shell=True)

        for seed in seeds:
            time.sleep(1.0)
            run_with_seed_and_runtime(seed, port)
            port += int(10e4)
        print("Last port = ", port)



    #endregion






    #region plot

    if sys.argv[1] == "--plot":
        import itertools
        import pandas as pd
        from matplotlib import pyplot as plt
        import numpy as np

        savefig_paths = ["results/figures", "/home/paran/Dropbox/BCAM/07_estancia_1/paper/images"]

        df_row_list = []
        for seed in seeds:
            res_filepath = f"results/data/halveruntime_results/{task}_halveruntime_exp_result_{seed}.txt"
            if exists(res_filepath):
                with open(res_filepath, "r") as f:
                    all_text = f.readlines()
                    for line in all_text:
                        split_line = line.strip("\n").split(",")
                        fitness = float(split_line[1])
                        clock_time = float(split_line[2])
                        rw_time = float(split_line[3])
                        _ = float(split_line[4])
                        evals = int(split_line[5])
                        maxevaltimes_each_controller = [float(el) for el in split_line[6].strip("()").split(";") if len(el) > 0]
                        if float(fitness) < -10e200:
                            continue
                        df_row_list.append([seed, evals, rw_time, fitness, maxevaltimes_each_controller])
        df_halve_maxevaltime = pd.DataFrame(df_row_list, columns=["seed", "evals", "rw_time", "fitness", "maxevaltimes_each_controller"])

        df_row_list = []
        for seed in seeds:
            res_filepath = f"results/data/runtimewrtmaxevaltime_results/{task}_runtimewrtmaxevaltime_exp_result_{seed}_maxEvalTime_{30.0}.txt"
            if exists(res_filepath):
                with open(res_filepath, "r") as f:
                    all_text = f.readlines()
                    for line in all_text:
                        split_line = line.strip("\n").split(",")
                        fitness = float(split_line[1])
                        clock_time = float(split_line[2])
                        rw_time = float(split_line[3])
                        maxEvalTime = float(split_line[4])
                        evals = int(split_line[5])
                        if float(fitness) < -10e200:
                            continue
                        df_row_list.append([seed, evals, rw_time, fitness])
        df_maxevaltime30_evaluations = pd.DataFrame(df_row_list, columns=["seed", "evals", "rw_time", "fitness"])

        if df_maxevaltime30_evaluations.empty or df_halve_maxevaltime.empty:
            print("Skipping task", task,", the dataframe is empty.")
            continue

        plt.figure()
        plt.xlim((0, max((max(df_maxevaltime30_evaluations["rw_time"]),max(df_halve_maxevaltime["rw_time"])))))

        plt.scatter(df_maxevaltime30_evaluations["rw_time"], df_maxevaltime30_evaluations["fitness"], marker="x", label="Constant runtime", alpha=0.5, color="green")
        plt.scatter(df_halve_maxevaltime["rw_time"], df_halve_maxevaltime["fitness"], marker="o", label = "halve runtime", alpha=0.5, color="red")
        plt.legend()
        for path in savefig_paths:
            plt.savefig(path + f"/{task}_halveruntime_exp_scatter.pdf")
        plt.close()


        rw_time_list_constant = sorted(df_maxevaltime30_evaluations["rw_time"].unique())
        x_constant = []
        y_constant_median = []
        y_constant_lower = []
        y_constant_upper = []

        for runtime in rw_time_list_constant:
            if df_maxevaltime30_evaluations[df_maxevaltime30_evaluations["rw_time"]==runtime].shape[0] <= 2:
                rw_time_list_constant.remove(runtime)
            else:
                x_constant.append(runtime)
                y_constant_median.append(df_maxevaltime30_evaluations[df_maxevaltime30_evaluations["rw_time"]==runtime]["fitness"].median())
                y_constant_lower.append(df_maxevaltime30_evaluations[df_maxevaltime30_evaluations["rw_time"]==runtime]["fitness"].quantile(q=0.25))
                y_constant_upper.append(df_maxevaltime30_evaluations[df_maxevaltime30_evaluations["rw_time"]==runtime]["fitness"].quantile(q=0.75))


        rw_time_list_halve = rw_time_list_constant
        x_halve = []
        y_halve_median = []
        y_halve_lower = []
        y_halve_upper = []



        # x_step_size = np.median(np.array(rw_time_list_constant[1:]) - np.array(rw_time_list_constant[:-1]))

        max_runtimes_seed = []
        for seed in seeds:
            runtime_seed = df_halve_maxevaltime[df_halve_maxevaltime["seed"]==seed]["rw_time"]
            if len(runtime_seed) != 0:
                max_runtimes_seed.append(max(runtime_seed))


        x_max = np.median(max_runtimes_seed)
        x_step_size = (x_max - min(df_halve_maxevaltime["rw_time"])) / len(df_halve_maxevaltime) * len(seeds)


        for runtime in np.arange(min(df_halve_maxevaltime["rw_time"]), x_max, x_step_size)[1:]:
            fitnesses = []
            for seed in seeds:
                f_with_seed_and_runtime_leq = df_halve_maxevaltime[(df_halve_maxevaltime["rw_time"]<=runtime) & (df_halve_maxevaltime["seed"]==seed)]["fitness"]
                if len(f_with_seed_and_runtime_leq) != 0:
                    fitnesses.append(max(f_with_seed_and_runtime_leq))
            if len(fitnesses) == 0:
                continue
            x_halve.append(runtime)
            y_halve_median.append(np.quantile(np.array(fitnesses), 0.5))
            y_halve_lower.append(np.quantile(np.array(fitnesses), 0.25))
            y_halve_upper.append(np.quantile(np.array(fitnesses), 0.75))
  


        plt.figure()
        plt.xlim((0, max((max(df_maxevaltime30_evaluations["rw_time"]),max(df_halve_maxevaltime["rw_time"])))))
        plt.plot(x_halve, y_halve_median, marker="", label="halve runtime", color="red")
        plt.fill_between(x_halve, y_halve_lower, y_halve_upper, color='red', alpha=.1)
        plt.plot(x_constant, y_constant_median, marker="", label="Constant runtime", color="green")
        plt.fill_between(x_constant, y_constant_lower, y_constant_upper, color='green', alpha=.1)
        #plt.scatter(df_halve_maxevaltime["rw_time"], df_halve_maxevaltime["fitness"], marker="o", label = "halve runtime", alpha=0.5, color="red")
        plt.legend()
        for path in savefig_paths:
            plt.savefig(path + f"/{task}_halveruntime_exp_line.pdf")
        plt.close()
        




        
        x_maxevaltime = []
        y_maxevaltime_median = []
        y_maxevaltime_lower = []
        y_maxevaltime_upper = []
        vertical_lines_30s_iteration = []

        for evals in sorted(df_halve_maxevaltime["evals"].unique()):
            maxevaltimes_each_controller_list = []
            for seed in seeds:
                if len(df_halve_maxevaltime[(df_halve_maxevaltime["evals"]==evals) & (df_halve_maxevaltime["seed"]==seed)]) != 1:
                    continue
                runtimes_with_certain_evals_and_seed = df_halve_maxevaltime[(df_halve_maxevaltime["evals"]==evals) & (df_halve_maxevaltime["seed"]==seed)]["maxevaltimes_each_controller"].iloc[0]
                y = np.mean(runtimes_with_certain_evals_and_seed)
                maxevaltimes_each_controller_list.append(y)
            if np.quantile(maxevaltimes_each_controller_list,0.5) > 29.5:
                vertical_lines_30s_iteration.append(evals)
                continue
            x_maxevaltime.append(evals)
            y_maxevaltime_median.append(np.quantile(np.array(maxevaltimes_each_controller_list), 0.5))
            y_maxevaltime_lower.append(np.quantile(np.array(maxevaltimes_each_controller_list), 0.25))
            y_maxevaltime_upper.append(np.quantile(np.array(maxevaltimes_each_controller_list), 0.75))

        plt.figure()
        plt.xlim((0, max(df_halve_maxevaltime["evals"])))
        plt.plot(x_maxevaltime, y_maxevaltime_median, marker="", label="Avg. maxEvalTime", color="red")

        if len(vertical_lines_30s_iteration) != 0:
            ymin, ymax = plt.gca().get_ylim() 
            plt.vlines(x=vertical_lines_30s_iteration, ymin=ymin, ymax=ymax, colors='black', ls='--', lw=2, label='reset stopping criterion')

        plt.fill_between(x_maxevaltime, y_maxevaltime_lower, y_maxevaltime_upper, color='red', alpha=.1)
        #plt.scatter(df_halve_maxevaltime["rw_time"], df_halve_maxevaltime["fitness"], marker="o", label = "halve runtime", alpha=0.5, color="red")
        plt.legend()
        for path in savefig_paths:
            plt.savefig(path + f"/{task}_halveruntime_exp_avgMaxEvalTime_line.pdf")
        plt.close()

        # pd.set_option('display.max_rows', None)
        # pd.set_option('display.max_columns', None)
        # pd.set_option('display.width', None)
        # pd.set_option('display.max_colwidth', -1)

        # print(df_halve_maxevaltime)
        # print(df_maxevaltime30_evaluations)
    #endregion


    print("done.")
