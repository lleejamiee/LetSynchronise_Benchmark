import os
import csv
import json


class Utilities:
    def __init__(self):
        pass

    def MsToNs(ms):
        return ms * 1000000

    def prepare_system(self, sys_config, task_set, dependencies):
        sys_config["EntityStore"] = task_set
        sys_config["DependencyStore"] = dependencies

        return sys_config

    def save_system(self, system, tasks_instances):
        system["EntityInstancesStore"] = tasks_instances

        directory = "output"
        base_filename = "system"
        extension = ".json"

        counter = 1
        while True:
            file_name = f"{base_filename}{counter:03d}{extension}"

            file_path = os.path.join(directory, file_name)

            if not os.path.exists(file_path):
                break

            counter += 1

        with open(file_path, "w") as outfile:
            json.dump(tasks_instances, outfile, indent=4)

        return counter, system

    def save_result(self, result, counter, system, goal, hyperperiod):
        fieldnames = [
            "index",
            "solution_time",
            "CPU_time",
            "sol_status",
            "num_variables",
            "num_constraints",
            "num_tasks",
            "num_instances",
            "hyperperiod",
        ]

        num_tasks = len(system["EntityStore"])

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
                        "index": counter,
                        "solution_time": result.solutionTime,
                        "CPU_time": result.solutionCpuTime,
                        "sol_status": result.sol_status,
                        "num_variables": result.numVariables(),
                        "num_constraints": result.numConstraints(),
                        "num_tasks": num_tasks,
                        "num_instances": num_instances,
                        "hyperperiod": hyperperiod,
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
                        "index": counter,
                        "solution_time": result.solutionTime,
                        "CPU_time": result.solutionCpuTime,
                        "sol_status": result.sol_status,
                        "num_variables": result.numVariables(),
                        "num_constraints": result.numConstraints(),
                        "num_tasks": num_tasks,
                        "num_instances": num_instances,
                        "hyperperiod": hyperperiod,
                        "average_delay": avg_delay,
                    }
                )
