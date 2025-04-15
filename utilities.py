import os
import csv
import json


class Utilities:
    def __init__(self):
        pass

    def MsToNs(ms):
        return ms * 1000000

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
        self, system, min_core_tasks_instances, min_e2e_task_instances, run
    ):
        min_e2e_system = system
        min_core_system = system
        min_e2e_system["EntityInstancesStore"] = min_core_tasks_instances
        min_core_system["EntityInstancesStore"] = min_e2e_task_instances

        directory = "system_config"
        min_e2e_base_filename = "min_e2e_system"
        min_core_base_filename = "min_core_system"
        extension = ".json"

        counter = 1
        while True:
            file_name = f"{min_core_base_filename}{counter:03d}-{run}{extension}"

            file_path = os.path.join(directory, file_name)

            if not os.path.exists(file_path):
                break

            counter += 1

        with open(file_path, "w") as outfile:
            json.dump(system, outfile, indent=4)

        file_path = os.path.join(
            directory, f"{min_e2e_base_filename}{counter:03d}-{run}{extension}"
        )
        with open(file_path, "w") as outfile:
            json.dump(system, outfile, indent=4)

        return counter, min_e2e_system, min_core_system

    def save_result(self, result, counter, system, goal, hyperperiod, utilisation, run):
        fieldnames = [
            "index",
            "solution_time",
            "CPU_time",
            "sol_status",
            "num_variables",
            "num_constraints",
            "num_devices",
            "num_cores",
            "num_tasks",
            "num_dependencies",
            "num_instances",
            "hyperperiod",
            "utilisation",
        ]

        num_devices = len(system["DeviceStore"])
        num_cores = len(system["CoreStore"])
        num_tasks = len(system["EntityStore"])
        num_dependencies = len(system["DependencyStore"])

        num_instances = 0
        for task in system["EntityInstancesStore"]:
            num_instances += len(task["value"])

        base_path = "results"

        if goal == "c":
            file_path = f"{base_path}/min_core_results.csv"
            write_header = not os.path.exists(file_path)

            core_count = 0
            for v in result.variables():
                if "u_" in v.name:
                    core_count += v.varValue

            with open(file_path, "a", newline="") as csvfile:
                fieldnames.append("num_cores_used")
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if write_header:
                    writer.writeheader()

                writer.writerow(
                    {
                        "index": f"{counter}-{run}",
                        "solution_time": result.solutionTime,
                        "CPU_time": result.solutionCpuTime,
                        "sol_status": result.sol_status,
                        "num_variables": result.numVariables(),
                        "num_constraints": result.numConstraints(),
                        "num_devices": num_devices,
                        "num_cores": num_cores,
                        "num_tasks": num_tasks,
                        "num_dependencies": num_dependencies,
                        "num_instances": num_instances,
                        "hyperperiod": hyperperiod,
                        "utilisation": utilisation,
                        "num_cores_used": core_count,
                    }
                )

        elif goal == "e2e":
            file_path = f"{base_path}/min_avg_e2e_results.csv"
            write_header = not os.path.exists(file_path)

            avg_delay = 0
            for v in result.variables():
                if "delay" in v.name:
                    avg_delay += v.varValue

            avg_delay = avg_delay / num_tasks

            with open(file_path, "a", newline="") as csvfile:
                fieldnames.append("average_delay")
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if write_header:
                    writer.writeheader()

                writer.writerow(
                    {
                        "index": f"{counter}-{run}",
                        "solution_time": result.solutionTime,
                        "CPU_time": result.solutionCpuTime,
                        "sol_status": result.sol_status,
                        "num_variables": result.numVariables(),
                        "num_constraints": result.numConstraints(),
                        "num_devices": num_devices,
                        "num_cores": num_cores,
                        "num_tasks": num_tasks,
                        "num_dependencies": num_dependencies,
                        "num_instances": num_instances,
                        "hyperperiod": hyperperiod,
                        "utilisation": utilisation,
                        "average_delay": avg_delay,
                    }
                )
