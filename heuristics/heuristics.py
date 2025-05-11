import os
import csv
import math
import copy
import json


def main():
    if not os.path.exists("system_config"):
        os.makedirs("system_config")
    if not os.path.exists("results"):
        os.makedirs("results")

    parent_dir = os.path.dirname(os.path.dirname(__file__))
    target_dir = parent_dir + "/system_config"

    # target_dir = os.path.join("system_config")
    max_utilisation = 1

    for entry in os.scandir(target_dir):
        if entry.is_file() and "DS" not in entry.path and "min_core" in entry.path:
            file = open(entry.path)
            data = json.load(file)
            num_cores = len(data["CoreStore"])

            cores = [0] * num_cores
            sorted_tasks = sort_tasks(data["EntityStore"])

            tasks1 = copy.deepcopy(sorted_tasks)
            tasks2 = copy.deepcopy(sorted_tasks)

            lowest_utilisation_tasks = lowest_utilisation(
                cores, tasks1, max_utilisation
            )
            lowest_core_index_tasks = lowest_core_index(cores, tasks2, max_utilisation)

            save_to_file(data, lowest_utilisation_tasks, entry.path, type="lu")
            save_to_file(data, lowest_core_index_tasks, entry.path, type="lci")


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
    core_index = 0
    task_index = 0

    while task_index < len(tasks):
        wcet = tasks[task_index]["wcet"]
        period = tasks[task_index]["period"]

        utilisation = wcet / period

        flag = False
        for core_index in range(len(cores)):
            sum_utilisation = utilisation + cores[core_index]

            if sum_utilisation <= max_utilisation:
                cores[core_index] = sum_utilisation

                tasks[task_index]["core"] = f"c{(core_index) + 1}"
                task_index += 1
                flag = True
                break

        if not flag:
            return None

    return tasks


def save_to_file(data, tasks, path, type):
    og_file_name = path.split("/")[-1]
    core_count = 0

    if tasks != None:
        data["EntityStore"] = tasks
        core_count = count_used_cores(tasks)

        file_name = ""
        if type == "lu":
            file_name = f"lu_{og_file_name}"
        elif type == "lci":
            file_name = f"lci_{og_file_name}"

        save_system_to_json(file_name, data)

    save_result(
        core_count,
        type="lowest_utilisation" if type == "lu" else "lowest_core_index",
        result=1 if tasks is not None else 0,
        og_file_name=og_file_name,
    )


def count_used_cores(tasks):
    used_cores = set()

    for task in tasks:
        used_cores.add(task["core"])

    return len(used_cores)


def save_system_to_json(file_name, system):
    directory = "system_config"
    file_path = os.path.join(directory, file_name)

    with open(file_path, "w") as outfile:
        json.dump(system, outfile, indent=4)


def save_result(core_count, type, result, og_file_name):
    field_names = ["og_file_name", "result", "core_count"]

    base_path = "results"
    file_path = f"{base_path}/{type}_results.csv"
    write_header = not os.path.exists(file_path)

    with open(file_path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)

        if write_header:
            writer.writeheader()

        writer.writerow(
            {"og_file_name": og_file_name, "result": result, "core_count": core_count}
        )


if __name__ == "__main__":
    main()
