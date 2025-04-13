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
    # Optimisation goal
    parser.add_argument("-g", type=str)

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

    # Check if required arguments have been passed in
    if args.t == None and args.u == None:
        print("Please specify either number of tasks, or system utiilisation value.")
        return 0

    if args.g == None:
        print("Please specify optimisation goal")
        return 0

    if args.g != "c" and args.g != "e2e":
        print("Please select valid optimisation goal (c or e2e)")
        return 0

    # Initialise variables
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

    # Generate tasks based on the number of task specified
    if args.t != None:
        task_set = task_generator.generate_with_task_limit(
            args.t, args.o, args.e, args.du
        )
    # Generate tasks based on the number of utilisation specified
    elif args.u != None:
        task_set = task_generator.generate_with_utilisation_limit(
            args.u, args.o, args.e, args.du
        )

    if args.t == None:
        args.t = len(task_set)

    if args.u == None:
        args.u = utilities.calculate_utilisation(task_set)

    if args.d == None:
        args.d = args.t * (args.t - 1) / 2

    # Generate system configuration (cores, devices, network delays)
    sys_config = sys_config_generator.generate_sys_config(
        args.c, args.dev, args.p, args.n
    )

    # Generate dependencies if there are more than 1 task in the task set
    if args.t > 1:
        dependencies = dependency_generator.generate_dependencies(args.d, task_set)

    # Prapare full system configuration for ILP calculation
    system = utilities.prepare_system(sys_config, task_set, dependencies)

    # Performa ILP calculation
    tasks_instances, result, hyperperiod = ilp_multicore.multicore_core_scheduler(
        system, args.g
    )

    # Save system configuration to file
    counter, system = utilities.save_system(system, tasks_instances)
    # Save result to file
    utilities.save_result(result, counter, system, args.g, hyperperiod, args.u)


if __name__ == "__main__":
    main()
