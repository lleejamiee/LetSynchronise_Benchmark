import os
import csv
import json
import copy


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
        counter,
        utilisation,
        run,
        config,
    ):
        fieldnames = [
            "index",
            "num_tasks",
            "num_instances",
            "utilisation",
            "e2e_core_count",
            "mc_core_count",
            "e2e_total_delay",
            "e2e_sol_time",
            "mc_sol_time",
            "e2e_sol_status",
            "mc_sol_status",
        ]

        num_tasks = len(min_e2e_system["EntityStore"])
        num_tasks_instances = 0
        for task in min_e2e_system["EntityInstancesStore"]:
            num_tasks_instances += len(task["value"])

        base_path = "results"

        e2e_used_cores = set()
        for v in min_e2e_result.variables():
            if (
                v.name.startswith("assigned_")
                and v.varValue != None
                and v.varValue == 1.0
            ):
                core_name = v.name.split("_'")[-1].rstrip("')")
                e2e_used_cores.add(core_name)

        min_core_core_count = 0
        for v in min_core_result.variables():
            if "u_" in v.name and v.varValue != None:
                min_core_core_count += v.varValue

        total_delay = 0
        for v in min_e2e_result.variables():
            if "delay" in v.name and v.varValue != None:
                total_delay += v.varValue

        file_path = f"{base_path}/physical_system{config:02d}_results.csv"
        write_header = not os.path.exists(file_path)

        with open(file_path, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if write_header:
                writer.writeheader()

            writer.writerow(
                {
                    "index": f"{counter}-{run}",
                    "num_tasks": num_tasks,
                    "num_instances": num_tasks_instances,
                    "utilisation": utilisation,
                    "e2e_core_count": len(e2e_used_cores),
                    "mc_core_count": min_core_core_count,
                    "e2e_total_delay": total_delay,
                    "e2e_sol_time": min_e2e_result.solutionTime,
                    "mc_sol_time": min_core_result.solutionTime,
                    "e2e_sol_status": min_e2e_result.sol_status,
                    "mc_sol_status": min_core_result.sol_status,
                }
            )
