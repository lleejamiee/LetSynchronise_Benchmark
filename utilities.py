import os
import csv
import json
import copy

from ilp.multicore import MultiCoreScheduler


class Utilities:
    def __init__(self):
        pass

    def MsToNs(ms):
        return ms * 1000000

    def extract_physical_systems(self, sys1_path, sys2_path):
        sys_configs = []

        system1 = open(sys1_path)
        sys_configs.append(json.load(system1))

        system2 = open(sys2_path)
        sys_configs.append(json.load(system2))

        return sys_configs

    def calculate_utilisation(self, task_set):
        utilisation = 0

        for task in task_set:
            utilisation += task["wcet"] / task["period"]

        return utilisation

    def prepare_system(self, sys_config, task_set, dependencies):
        sys_config["EntityStore"] = task_set
        sys_config["DependencyStore"] = dependencies

        return sys_config

    def save_system(
        self,
        system,
        min_e2e_task_instances,
        min_core_tasks_instances,
        run,
        config,
        counter,
        successful
    ):
        min_e2e_system = copy.deepcopy(system)
        min_core_system = copy.deepcopy(system)

        min_e2e_system["EntityInstancesStore"] = min_e2e_task_instances
        min_core_system["EntityInstancesStore"] = min_core_tasks_instances

        directory = "system_config"
        min_e2e_base_filename = "min_e2e_system"
        min_core_base_filename = "min_core_system"
        extension = ".json"

        while True:
            file_name = (
                f"{config:02d}-{min_core_base_filename}{counter:03d}-{run}{extension}"
            )

            file_path = os.path.join(directory, file_name)

            if not os.path.exists(file_path):
                break

            counter += 1

        with open(file_path, "w") as outfile:
            json.dump(min_core_system, outfile, indent=4)

        file_path = os.path.join(
            directory,
            f"{config:02d}-{min_e2e_base_filename}{counter:03d}-{run}{extension}",
        )
        with open(file_path, "w") as outfile:
            json.dump(min_e2e_system, outfile, indent=4)

        return counter, min_e2e_system, min_core_system

    def save_result(
        self,
        min_e2e_result,
        min_e2e_system,
        min_core_result,
        min_core_result_e2e,
        counter,
        utilisation,
        run,
        config,
    ):
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
            "e2e_core_count",
            "mc_core_count",
            "e2e_total_delay",
            "mc_total_delay",
            "e2e_bottom_dependencies",
            "mc_bottom_dependencies",
            "e2e_average_delay",
            "mc_average_delay",
            "e2e_objective",
            "mc_objective",
            "e2e_sol_time",
            "mc_sol_time",
            "e2e_sol_status",
            "mc_sol_status",

            # Gurobi-specific results
            "e2e_num_constrs",
            "mc_num_consts",
            "e2e_num_vars",
            "mc_num__vars",
            "e2e_num_int_vars",
            "mc_num_int_vars",
            "e2e_num_bin_vars",
            "mc_num_bin_vars",
            "e2e_runtime",
            "mc_runtime",
            "e2e_work",
            "mc_work",
            "e2e_mem_used",
            "mc_mem_used",
            "e2e_max_mem_used",
            "mc_max_mem_used",
            "e2e_status",
            "mc_status",
        ]

        task_set = min_e2e_system["EntityStore"]
        num_tasks = len(task_set)

        num_tasks_instances = 0
        for task in min_e2e_system["EntityInstancesStore"]:
            num_tasks_instances += len(task["value"])
        
        dependency_set = min_e2e_system["DependencyStore"]
        num_task_dependencies = len(dependency_set)
        
        num_instance_dependencies = 0
        for dependency in dependency_set:
            task = next((x for x in min_e2e_system["EntityInstancesStore"] if x["name"] == dependency["destination"]["task"]), None)
            if task != None:
                num_instance_dependencies += len(task["value"])

        base_path = "results"
        file_path = f"{base_path}/physical_system{config:02d}_results.csv"
        write_header = not os.path.exists(file_path)

        with open(file_path, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if write_header:
                writer.writeheader()

            writer.writerow(
                {
                    # Generic fields
                    "index": f"{counter}-{run}",
                    "num_tasks": num_tasks,
                    "num_instances": num_tasks_instances,
                    "num_task_dependencies": num_task_dependencies,
                    "num_instance_dependencies": num_instance_dependencies,
                    "utilisation": utilisation,
                    "hyperperiod": MultiCoreScheduler.calculate_hyperperiod(task_set),
                    "hyperoffset": MultiCoreScheduler.calculate_hyperoffset(task_set),
                    "makespan": MultiCoreScheduler.calculate_makespan(task_set),
                    "largeN": MultiCoreScheduler.calculate_largeN(task_set),

                    # ILP results
                    "e2e_core_count": self.get_num_used_cores(min_e2e_result),
                    "mc_core_count": self.get_num_used_cores(min_core_result),
                    "e2e_total_delay": self.get_total_delay(min_e2e_result),
                    "mc_total_delay": self.get_total_delay(min_core_result_e2e),
                    "e2e_bottom_dependencies": self.get_bottom_dependencies(min_e2e_result),
                    "mc_bottom_dependencies": self.get_bottom_dependencies(min_core_result_e2e),
                    "e2e_average_delay": self.get_average_delay(min_e2e_result),
                    "mc_average_delay": self.get_average_delay(min_core_result_e2e),
                    "e2e_objective": min_e2e_result.objective.value(),
                    "mc_objective": min_core_result.objective.value(),
                    "e2e_sol_time": min_e2e_result.solutionCpuTime,
                    "mc_sol_time": min_core_result.solutionCpuTime,
                    "e2e_sol_status": min_e2e_result.sol_status,
                    "mc_sol_status": min_core_result.sol_status,

                    # Gurobi-specific results
                    "e2e_num_constrs": min_e2e_result.solverModel.NumConstrs,
                    "mc_num_consts": min_core_result.solverModel.NumConstrs,
                    "e2e_num_vars": min_e2e_result.solverModel.NumVars,
                    "mc_num__vars": min_core_result.solverModel.NumVars,
                    "e2e_num_int_vars": min_e2e_result.solverModel.NumIntVars,
                    "mc_num_int_vars": min_core_result.solverModel.NumIntVars,
                    "e2e_num_bin_vars": min_e2e_result.solverModel.NumBinVars,
                    "mc_num_bin_vars": min_core_result.solverModel.NumBinVars,
                    "e2e_runtime": min_e2e_result.solverModel.Runtime,
                    "mc_runtime": min_core_result.solverModel.Runtime,
                    "e2e_work": min_e2e_result.solverModel.Work,
                    "mc_work": min_core_result.solverModel.Work,
                    "e2e_mem_used": min_e2e_result.solverModel.MemUsed,
                    "mc_mem_used": min_core_result.solverModel.MemUsed,
                    "e2e_max_mem_used": min_e2e_result.solverModel.MaxMemUsed,
                    "mc_max_mem_used": min_core_result.solverModel.MaxMemUsed,
                    "e2e_status": min_e2e_result.solverModel.Status,
                    "mc_status": min_core_result.solverModel.Status,
                }
            )
    
    @staticmethod
    def get_num_used_cores(result):
        for v in result.variables():
            if "cores_used" in v.name and v.varValue != None:
                return v.varValue
    
        return -1
    
    @staticmethod
    def get_total_delay(result):
        for v in result.variables():
            if "total_delay" in v.name and v.varValue != None:
                return v.varValue
    
        return -1

    @staticmethod
    def get_bottom_dependencies(result):
        bottom_dependencies = 0
        for v in result.variables():
            if "bool_dep" in v.name and "__1" in v.name and v.varValue == 1.0:
                bottom_dependencies += 1
    
        return bottom_dependencies

    @staticmethod
    def get_average_delay(result):
        sum = 0
        count = 0
        for v in result.variables():
            if "bool_dep" in v.name and "__1" not in v.name and v.varValue == 1.0:
                v_delay = result.variablesDict()[v.name.replace("bool_dep", "delay")]
                if v_delay != None:
                    sum += v_delay.varValue
                    count += 1
        
        if count > 0:
            return sum / count
        
        return -1

