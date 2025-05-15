import os
import csv
import math
import copy
import json

from ilp.multicore import MultiCoreScheduler
from utilities import Utilities

MAX_UTILISATIONS = [1]
BASE_FILENAME = "min_e2e"

def main():

    ilp_multicore = MultiCoreScheduler()

    target_dir = os.path.join("system_config")

    for physical_system in sorted(os.scandir(target_dir), key=lambda e: e.name):
        if physical_system.is_dir():
            solved_dir = os.path.join(physical_system.path, "Solved")
            for system in sorted(os.scandir(solved_dir), key=lambda e: e.name):
                if system.is_file() and "DS" not in system.path and BASE_FILENAME in system.path:
                    file = open(system.path)
                    
                    data = json.load(file)
                    data["EntityInstancesStore"] = []

                    num_cores = len(data["CoreStore"])
                    cores = [0] * num_cores

                    sorted_tasks = sort_tasks(data["EntityStore"])

                    for max_utilisation in MAX_UTILISATIONS:
                        cores_lowest_util = copy.deepcopy(cores)
                        cores_lowest_core = copy.deepcopy(cores)

                        tasks_lowest_util = copy.deepcopy(sorted_tasks)
                        tasks_lowest_core = copy.deepcopy(sorted_tasks)

                        tasks_lowest_util = lowest_utilisation(cores_lowest_util, tasks_lowest_util, max_utilisation)
                        tasks_lowest_core = lowest_core_index(cores_lowest_core, tasks_lowest_core, max_utilisation)

                        system_lowest_util = copy.deepcopy(data)
                        system_lowest_core = copy.deepcopy(data)

                        system_lowest_util["EntityStore"] = tasks_lowest_util
                        system_lowest_core["EntityStore"] = tasks_lowest_core

                        lowest_util_instances, lowest_util_result_e2e = (
                            ilp_multicore.multicore_core_scheduler(system_lowest_util, "e2e")
                        )
                        lowest_core_instances, lowest_core_result_e2e = (
                            ilp_multicore.multicore_core_scheduler(system_lowest_core, "e2e")
                        )

                        system_lowest_util["EntityInstancesStore"] = lowest_util_instances
                        system_lowest_core["EntityInstancesStore"] = lowest_core_instances

                        save_system(system_lowest_util, system.path, "heur_util_"+str(max_utilisation))
                        save_system(system_lowest_core, system.path, "heur_core_"+str(max_utilisation))

                        index = system.name.replace(BASE_FILENAME+"_system", "").replace(".json", "")
                        save_results(system_lowest_util, lowest_util_result_e2e, lowest_core_result_e2e, physical_system.name, max_utilisation, index)


def sort_tasks(tasks):
    tasks.sort(key=lambda x: x["wcet"] / x["period"], reverse=True)
    return tasks


def lowest_utilisation(cores, tasks, max_utilisation):
    for task in tasks:
        wcet = task["wcet"]
        period = task["period"]

        utilisation = wcet / period

        min_value = min(cores)
        min_index = cores.index(min_value)

        sum_utilisation = min_value + utilisation

        if sum_utilisation <= max_utilisation:
            cores[min_index] = sum_utilisation

            task["core"] = f"c{min_index + 1}"
        else:
            return None

    return tasks


def lowest_core_index(cores, tasks, max_utilisation):
    for task in tasks:
        wcet = task["wcet"]
        period = task["period"]

        utilisation = wcet / period

        flag = False
        for core_index in range(len(cores)):
            sum_utilisation = utilisation + cores[core_index]

            if sum_utilisation <= max_utilisation:
                cores[core_index] = sum_utilisation

                task["core"] = f"c{(core_index) + 1}"
                flag = True
                break

        if not flag:
            return None

    return tasks

def save_system(system, original_path, type):
    new_filename = original_path.replace(BASE_FILENAME, type)

    with open(new_filename, "w") as outfile:
        json.dump(system, outfile, indent=4)

def save_results(system, lowest_util_result, lowest_core_result, config, max_utilisation, index):
    fieldnames = [
        # Generic fields
        "index",
        "num_tasks",
        "num_instances",
        "num_task_dependencies",
        "num_instance_dependencies",
        "hyperperiod",
        "hyperoffset",
        "makespan",
        "largeN",
        "utilisation",

        # ILP results
        "lu_core_count",
        "lc_core_count",
        "lu_total_delay",
        "lc_total_delay",
        "lu_bottom_dependencies",
        "lc_bottom_dependencies",
        "lu_average_delay",
        "lc_average_delay",
        "lu_sol_status",
        "lc_sol_status",

        # Gurobi-specific results
        "lu_status",
        "lc_status",
    ]

    task_set = system["EntityStore"]
    num_tasks = len(task_set)

    num_tasks_instances = 0
    for task in system["EntityInstancesStore"]:
        num_tasks_instances += len(task["value"])
    
    dependency_set = system["DependencyStore"]
    num_task_dependencies = len(dependency_set)
    
    num_instance_dependencies = 0
    for dependency in dependency_set:
        task = next((x for x in system["EntityInstancesStore"] if x["name"] == dependency["destination"]["task"]), None)
        if task != None:
            num_instance_dependencies += len(task["value"])

    base_path = "results"
    file_path = f"{base_path}/physical_system{config}_results_heur_{max_utilisation}.csv"
    write_header = not os.path.exists(file_path)

    with open(file_path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        writer.writerow(
            {
                # Generic fields
                "index": index,
                "num_tasks": num_tasks,
                "num_instances": num_tasks_instances,
                "num_task_dependencies": num_task_dependencies,
                "num_instance_dependencies": num_instance_dependencies,
                "utilisation": Utilities.calculate_utilisation(task_set),
                "hyperperiod": MultiCoreScheduler.calculate_hyperperiod(task_set),
                "hyperoffset": MultiCoreScheduler.calculate_hyperoffset(task_set),
                "makespan": MultiCoreScheduler.calculate_makespan(task_set),
                "largeN": MultiCoreScheduler.calculate_largeN(task_set),

                # ILP results
                "lu_core_count": Utilities.get_num_used_cores(lowest_util_result),
                "lc_core_count": Utilities.get_num_used_cores(lowest_core_result),
                "lu_total_delay": Utilities.get_total_delay(lowest_util_result),
                "lc_total_delay": Utilities.get_total_delay(lowest_core_result),
                "lu_bottom_dependencies": Utilities.get_bottom_dependencies(lowest_util_result),
                "lc_bottom_dependencies": Utilities.get_bottom_dependencies(lowest_core_result),
                "lu_average_delay": Utilities.get_average_delay(lowest_util_result),
                "lc_average_delay": Utilities.get_average_delay(lowest_core_result),
                "lu_sol_status": lowest_util_result.sol_status,
                "lc_sol_status": lowest_core_result.sol_status,

                # Gurobi-specific results
                "lu_status": lowest_util_result.solverModel.Status,
                "lc_status": lowest_core_result.solverModel.Status,
            }
        )

if __name__ == "__main__":
    main()
