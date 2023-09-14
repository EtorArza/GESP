import csv
import os
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
from typing import Callable, Any, Iterable, Tuple
from tqdm import tqdm as tqdm
from copy import deepcopy

class ObjectiveLogger:
    def __init__(self, file_path, replace_existing=False, logevery=1):
        # Create the directory if it doesn't exist
        log_dir = os.path.dirname(file_path)
        self.logevery=logevery
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Check if the log file already exists
        if os.path.exists(file_path):
            if replace_existing:
                os.remove(file_path)
            else:
                raise FileExistsError(f"The log file '{file_path}' already exists.")

        self.file_path = file_path
        self.row_count = 0  # Initialize row count

        # Open the file and create the CSV writer
        self.csvfile = open(self.file_path, 'a', newline='')
        self.writer = csv.writer(self.csvfile)

        self.header_written = False


    def log_values(self, time, values):

        if not self.header_written:
            # Write header row
            self.writer.writerow(["time"] + list(range(len(values[::self.logevery]))))
            self.header_written = True


        # Increment row count and add it as the first value
        self.row_count += 1

        # # Round objective values to 3 decimals
        # rounded_values = [round(val, 3) for val in values]

        values = values[::self.logevery]

        # Write the row
        self.writer.writerow([time] + list(values))

    def close(self):
        # Close the CSV file
        self.csvfile.close()

class tgrace_exp_figures():


    def __init__(self, experiment_name, experiment_result_path):

        def get_seed_from_filepath(filepath:str):
            return int(filepath.split("_")[-1].removesuffix(".txt"))

        self.combined_df: pd.DataFrame = None
        self.seed_list = []
        self.experiment_name = experiment_name
        filename_list = os.listdir(experiment_result_path)
        filename_list = filter(lambda x: ".txt" in x, filename_list)
        filename_list = sorted(filename_list, key=lambda x: get_seed_from_filepath(x))
        for filename in filename_list:
            if filename.startswith(experiment_name):
                file_path = os.path.join(experiment_result_path, filename)
                seed = get_seed_from_filepath(filename)
                self.seed_list.append(seed)
                df = pd.read_csv(file_path)
                df.insert(0, "seed", seed)
                self.combined_df = pd.concat([self.combined_df, df], axis=0).reset_index(drop=True)
        self.drop_seeds_with_low_time()
        self.reset_refs_stopping()
        self.ref_len = None




    def drop_seeds_with_low_time(self):
        prop_maxtime_drop = 0.9
        max_time_indices = self.combined_df.groupby('seed')['time'].idxmax()
        self.t_max = max(self.combined_df.loc[max_time_indices]["time"]) * prop_maxtime_drop
        max_time_rows = self.combined_df.loc[max_time_indices]["time"]


        print(f"Drop rows with a total time lower than {prop_maxtime_drop} * max_time.")
        filtered_series = max_time_rows[max_time_rows < self.t_max]
        indexes_below_0_9 = filtered_series.index.tolist()
        for idx_to_drop in indexes_below_0_9:
            seed = int(self.combined_df.loc[idx_to_drop]["seed"])
            self.combined_df = self.combined_df[self.combined_df['seed'] != seed]
        self.combined_df.reset_index(drop=True)
        self.seed_list = list(self.combined_df["seed"].unique())
        print(f"{len(indexes_below_0_9)} seeds where discarded, and a total of {len(self.seed_list)} valid seeds are left.")


    def reset_refs_stopping(self):
        self.gesp_refs = None
        self.gesp_current_steps = [0]
        self.gesp_current_steps_w_gesp = [0]
        self.gesp_current_best_f = [-1e9]
        self.gesp_current_best_f_w_gesp = [-1e9]


    def _get_ratio_where_gesp_worse(self):
        # It needs to be the value at the end. Otherwise the time graph makes no sense.
        w_gesp_f = self.gesp_current_best_f_w_gesp[-1]
        w_gesp_step = self.gesp_current_steps_w_gesp[-1]
        wo_gesp_f = None

        for step,f in zip(self.gesp_current_steps, self.gesp_current_best_f):
            if step > w_gesp_step:
                break
            wo_gesp_f = f
        assert wo_gesp_f != None
        comp = lambda a, b: 0.5 if a == b else 1 if a > b else 0
        return comp(wo_gesp_f, w_gesp_f) # without gesp better -> 1.0 

        # This is the old code, in which we compute which is better for every time step
        # is_with_gesp_better = []
        # i_gesp=0
        # for step, f in zip(self.gesp_current_steps, self.gesp_current_best_f):
        #     if step > self.gesp_current_steps_w_gesp[-1]:
        #         break
        #     while i_gesp < len(self.gesp_current_steps_w_gesp) and self.gesp_current_steps_w_gesp[i_gesp] <= step:
        #         comp = lambda a, b: 0.5 if a == b else 1 if a > b else 0
        #         is_gesp_better = comp(self.gesp_current_best_f_w_gesp[i_gesp], f) 
        #         i_gesp+=1
        #     is_with_gesp_better.append(is_gesp_better)
        # return is_with_gesp_better[-1] 

    def when2stopGESP(self, f_array, t_grace_proportion):
        is_better_than_best_found = f_array[-1] > self.gesp_refs[-1] if not self.gesp_refs is None else True
        assert self.ref_len is None or self.ref_len == len(f_array), "f_array should not change." 
        assert t_grace_proportion <= 1.0

        # First call
        if self.gesp_refs is None:
            self.gesp_refs = f_array[:]
            self.ref_len = len(f_array)
            ev_steps_with_gesp_this_episode = len(f_array)
        else:
            grace_steps = round(t_grace_proportion * len(f_array))
            indices =  np.where(
                np.maximum(       f_array[:len(f_array)-grace_steps],        f_array[grace_steps:]) < 
                np.minimum(self.gesp_refs[:len(f_array)-grace_steps], self.gesp_refs[grace_steps:])
            )[0]

            if indices.size > 0:
                ev_steps_with_gesp_this_episode = indices[0] + grace_steps + 1
                # print("Stop at step", ev_steps_with_gesp_this_episode)
            else:
                # print("No stop.")
                ev_steps_with_gesp_this_episode = len(f_array)
                if f_array[-1] > self.gesp_refs[-1]:
                    # print("Replacing refs.")
                    self.gesp_refs = f_array[:]

        was_early_stopped = ev_steps_with_gesp_this_episode != len(f_array)

        self.gesp_current_steps.append(self.gesp_current_steps[-1] + len(f_array))
        self.gesp_current_best_f.append(max(self.gesp_current_best_f[-1], f_array[-1]))
        self.gesp_current_steps_w_gesp.append(self.gesp_current_steps_w_gesp[-1] + ev_steps_with_gesp_this_episode)
        self.gesp_current_best_f_w_gesp.append(self.gesp_refs[-1])
        
        

        res = {
            "number_of_frames_evaluated": ev_steps_with_gesp_this_episode,
            "is_better_than_best_found": is_better_than_best_found,
            "was_early_stopped": was_early_stopped,
        }

        return res



    def get_proportion_timesaved_bestsolsmised(self, when2stopfunc, t_start_recording):
        """
        when2stopfunc: Given a array of f-values, it tells you the index in which the evaluation would be stopped. 
        """
        proportion_best_missed_list = []
        proportion_frames_evaluated_list = []
        proportion_with_gesp_worse_list = []
        assert self.combined_df.shape[0] > 2, "Dataframe is empty or has only one row."
        for seed in self.seed_list:
            self.reset_refs_stopping()
            iterable_of_observed_f = [el[1][2:].to_numpy() for el in self.combined_df[self.combined_df['seed'] == seed].iterrows()]
            res_list = [when2stopfunc(row) for row in iterable_of_observed_f]
            was_best_found_missed = [res["is_better_than_best_found"] and res["was_early_stopped"] for res in res_list if res["is_better_than_best_found"]]
            proportion_best_missed = np.mean(np.int16(was_best_found_missed))
            proportion_frames_evaluated = np.mean([res["number_of_frames_evaluated"] for res in res_list]) / (res_list[0]["number_of_frames_evaluated"]) # In the first evaluation all frames will be evaluated.
            proportion_best_missed_list.append(proportion_best_missed)
            proportion_frames_evaluated_list.append(proportion_frames_evaluated)
            proportion_with_gesp_worse_list.append(self._get_ratio_where_gesp_worse())
        return proportion_best_missed_list, proportion_frames_evaluated_list, proportion_with_gesp_worse_list


    def plot_tgrace_param(self):
        
        x = np.linspace(0.2, 1.0, 30, endpoint=True)
        y_missed_median = np.zeros_like(x)
        y_missed_upper_75 = np.zeros_like(x)
        y_missed_lower_75 = np.zeros_like(x)
        y_frames_median = np.zeros_like(x)
        y_frames_upper_75 = np.zeros_like(x)
        y_frames_lower_75 = np.zeros_like(x)
        y_better_median = np.zeros_like(x)
        y_better_upper_75 = np.zeros_like(x)
        y_better_lower_75 = np.zeros_like(x)

        for i, t_grace in tqdm(list(enumerate(x))):
            proportion_best_missed_list, proportion_frames_evaluated_list, proportion_with_gesp_better = self.get_proportion_timesaved_bestsolsmised(lambda x: self.when2stopGESP(x, t_grace), 0.0)
            x[i] = t_grace
            y_missed_median[i] = np.quantile(proportion_best_missed_list, 0.5)
            y_missed_upper_75[i] = np.quantile(proportion_best_missed_list, 0.75)
            y_missed_lower_75[i] = np.quantile(proportion_best_missed_list, 0.25)
            y_frames_median[i] = np.quantile(proportion_frames_evaluated_list, 0.5)
            y_frames_upper_75[i] = np.quantile(proportion_frames_evaluated_list, 0.75)
            y_frames_lower_75[i] = np.quantile(proportion_frames_evaluated_list, 0.25)
            y_better_median[i] = np.quantile(proportion_with_gesp_better, 0.5)
            y_better_upper_75[i] = np.quantile(proportion_with_gesp_better, 0.75)
            y_better_lower_75[i] = np.quantile(proportion_with_gesp_better, 0.25)

        plt.plot(x, y_missed_median, linestyle="-", color="#1f77b4", label="missed new best solution")
        plt.plot(x, y_frames_median, linestyle="--", color="#ff7f0e", label="steps computed")
        plt.plot(x, y_better_median, linestyle="-.", color="#2ca02c", label="worse with gesp")

        plt.xlabel(r"$t_{grace}$")
        plt.legend(title="Proportion of...")
        plt.savefig(f"results/figures/tgrace_experiment/{self.experiment_name}_proportion_average_no_runtime.pdf")


    def plot_tgrace_param_with_time(self):

        print("Calculations on intervals during the opitmization procedure.")
        n_time_partition = 11
        n_tgrace_partitions = 11
        res_matrix = np.zeros(shape=(n_tgrace_partitions, n_time_partition))
        original_df = deepcopy(self.combined_df)
        progress_bar = tqdm(total=n_tgrace_partitions*n_time_partition*3)


        for plotname, residx in zip(["bestmissed","framesevalutaed","withgespbetter"], [0,1,2]):
            t_partition_prev = 0.0
            t_partition_values = list(np.linspace(0.0,self.t_max, num=n_time_partition+2))[1:-1]
            t_grace_values = list(np.linspace(0.0, 1.0, num=n_tgrace_partitions, endpoint=True))
            for j, t_partition in enumerate(t_partition_values):
                self.combined_df = self.combined_df[(self.combined_df['time'] < t_partition)]
                for i, t_grace in enumerate(t_grace_values):
                    res = self.get_proportion_timesaved_bestsolsmised(lambda x: self.when2stopGESP(x, t_grace), t_partition_prev)[residx]
                    res_matrix[(i,j)] = np.mean(res)
                    progress_bar.update(1)
                self.combined_df = deepcopy(original_df)
                t_partition_prev = t_partition
            vmin = min((1.0-np.max(res_matrix), np.min(res_matrix)))
            vmax = 1.0 - vmin
            plt.imshow(res_matrix, cmap='viridis', interpolation='nearest', vmin=vmin, vmax=vmax)
            plt.colorbar(label='Values')
            plot_titles = ['Proportion in which with gesp missed \nan actually better solution.',
                           'Proportion of frames evaluated when \nusing GESP.',
                           'Probability that with gesp the score is \nworse for the same amount of steps.\n$t_{max}$ es distinto dependiendo de $t_{grace}$',]
            plt.title(plot_titles[residx])
            plt.yticks(range(len(t_grace_values)), ["{:.2f}".format(x) for x in t_grace_values])

            if residx == 2:
                plt.xticks(range(len(t_partition_values)), ["{:.1f}".format(x / (len(t_partition_values)-1)) for x in range(len(t_partition_values))])
                plt.xlabel(r"time with respect to $t_{max}$")
            else:
                plt.xticks(range(len(t_partition_values)), ["{:.1f}".format(x/3600) for x in t_partition_values])
                plt.xlabel("time (hours)")
            plt.ylabel(r"$t_{grace}$")
            plt.grid(visible=False)
            plt.tight_layout()
            plt.savefig(f"results/figures/tgrace_experiment/{self.experiment_name}_proportion_{plotname}.pdf")
            plt.close()





# Call the function with default parameters
exp = tgrace_exp_figures("veenstra", "results/data/tgrace_experiment/")
exp.plot_tgrace_param_with_time()
exp.plot_tgrace_param()
