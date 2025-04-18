import os
import argparse
from utilities import Utilities
from ilp.multicore import MultiCoreScheduler
from random_generators.task_set_generator import TaskSetGenerator
from random_generators.system_config_generator import SystemConfigGenerator
from random_generators.dependency_set_generator import DependencySetGenerator


def main():
    utilities = Utilities()
    parser = argparse.ArgumentParser()
    task_generator = TaskSetGenerator()
    ilp_multicore = MultiCoreScheduler()
    sys_config_generator = SystemConfigGenerator()
    dependency_generator = DependencySetGenerator()

    # CPU Utilisation
    parser.add_argument("-u", type=float)
    # Number of tasks to generate
    parser.add_argument("-t", type=int)
    # Number of dependencies to generate
    parser.add_argument("-d", type=int)
    # Maximum initial offset value
    parser.add_argument("-o", type=float)
    # Maximum WCET value
    parser.add_argument("-e", type=float)
    # Maximum duration value
    parser.add_argument("-du", type=float)
    # System config import
    parser.add_argument("-f", type=str)

    # Number of cores to generate
    parser.add_argument("-c", type=int)
    # Number of devices to generate
    parser.add_argument("-dev", type=int)
    # Maximum WCDT for protocol delay
    parser.add_argument("-p", type=float)
    # Maximum WCDT for network delay
    parser.add_argument("-n", type=float)

    args = parser.parse_args()
    del parser

    if not os.path.exists("system_config"):
        os.makedirs("system_config")
    if not os.path.exists("results"):
        os.makedirs("results")

    task_set = None
    dependencies = None

    # Initialise variables
    if args.t == None:
        args.t = 1

    if args.u == None:
        args.u = 0

    if args.o == None:
        args.o = 2000000
    else:
        args.o = utilities.MsToNs(args.o)

    if args.e == None:
        args.e = 1000000
    else:
        args.e = utilities.MsToNs(args.o)

    if args.du == None:
        args.du = 8000000
    else:
        args.du = utilities.MsToNs(args.du)

    if args.c == None:
        args.c = 3

    if args.dev == None:
        args.dev = 2

    if args.p == None:
        args.p = 600000
    else:
        args.p = utilities.MsToNs(args.p)

    if args.n == None:
        args.n = 1000000
    else:
        args.n = utilities.MsToNs(args.n)

    physical_sys1 = "physical_system/physical_system-01.json"
    physical_sys2 = "physical_system/physical_system-02.json"
    if not os.path.exists(physical_sys1) and not os.path.exists(physical_sys2):
        sys_configs = sys_config_generator.generate_sys_config(
            args.c, args.dev, args.p, args.n
        )
    else:
        sys_configs = utilities.extract_physical_systems(physical_sys1, physical_sys2)

    while True:
        # Run the ILP multiple times to see if there are any outliers
        for i in range(len(sys_configs)):
            solvable_count = 0
            run = 1
            # it needs to be 10 solvable
            counter = 1
            while solvable_count < 10:
                task_set = task_generator.generate_with_task_limit(
                    args.t, args.o, args.e, args.du
                )

                # If the utilisation is gt number of cores, break the loop
                args.u = utilities.calculate_utilisation(task_set)
                if args.u > len(sys_configs[i]["CoreStore"]):
                    break

                args.d = args.t * (args.t - 1) / 2
                dependencies = dependency_generator.generate_dependencies(
                    args.d, task_set
                )
                system = utilities.prepare_system(
                    sys_configs[i], task_set, dependencies
                )

                min_e2e_tasks_instances, min_e2e_result = (
                    ilp_multicore.multicore_core_scheduler(system, "e2e")
                )

                min_core_tasks_instances, min_core_result = (
                    ilp_multicore.multicore_core_scheduler(system, "c")
                )

                if min_core_result.sol_status == 1 and min_e2e_result.sol_status == 1:
                    solvable_count += 1

                counter, min_e2e_system, min_core_system = utilities.save_system(
                    system,
                    min_core_tasks_instances,
                    min_e2e_tasks_instances,
                    run,
                    i + 1,
                    counter,
                )

                utilities.save_result(
                    min_e2e_result,
                    min_e2e_system,
                    min_core_result,
                    counter,
                    args.u,
                    run,
                    i + 1,
                )

                run += 1

        args.t += 1


if __name__ == "__main__":
    main()
