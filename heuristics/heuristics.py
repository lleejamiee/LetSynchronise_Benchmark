import os
import json


def main():
    if not os.path.exists("system_config"):
        os.makedirs("system_config")

    # parent_dir = os.path.dirname(os.path.dirname(__file__))
    # target_dir = parent_dir + "/system_config"

    target_dir = os.path.join("system_config")
    max_utilisation = 1

    for entry in os.scandir(target_dir):
        if entry.is_file() and "DS" not in entry.path:
            file = open(entry.path)
            data = json.load(file)
            num_cores = len(data["CoreStore"])

            cores = [0] * num_cores
            tasks = data["EntityStore"]

            lowest_utilisation_tasks = lowest_utilisation(cores, tasks, max_utilisation)
            lowest_core_index_tasks = lowest_core_index(cores, tasks, max_utilisation)


def lowest_utilisation(cores, tasks, max_utilisation):
    for task in tasks:
        wcet = task["wcet"]
        period = task["period"]

        utilisation = wcet / period

        min_value = min(cores)
        min_index = cores.index(min_value)

        sum_utilisation = min_value + utilisation

        if sum_utilisation < max_utilisation:
            cores[min_index] = sum_utilisation

            task["core"] = f"c{min_index + 1}"
        else:
            print("unschedulable")

            return None

    return tasks


def lowest_core_index(cores, tasks, max_utilisation):
    core_index = 0
    task_index = 0

    while task_index < len(tasks):
        wcet = tasks[task_index]["wcet"]
        period = tasks[task_index]["period"]

        utilisation = wcet / period
        sum_utilisation = utilisation + cores[core_index]

        if sum_utilisation < max_utilisation:
            cores[core_index] = sum_utilisation

            tasks[task_index]["core"] = f"c{core_index + 1}"
            task_index += 1
        elif core_index < len(cores):
            core_index += 1
        else:
            print("unschedulable")

            return None

    return tasks


if __name__ == "__main__":
    main()
