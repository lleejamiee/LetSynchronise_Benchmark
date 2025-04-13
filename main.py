import os
import argparse
from utilities import Utilities
from ilp.multicore import MultiCoreScheduler
from random_generators.task_set_generator import TaskSetGenerator
from random_generators.system_config_generator import SystemConfigGenerator
from random_generators.dependency_set_generator import DependencySetGenerator


def main():
    parser = argparse.ArgumentParser()
    utilities = Utilities()
    sys_config_generator = SystemConfigGenerator()
    task_generator = TaskSetGenerator()
    dependency_generator = DependencySetGenerator()
    ilp_multicore = MultiCoreScheduler()

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

    if not os.path.exists("output"):
        os.makedirs("output")
    if not os.path.exists("results"):
        os.makedirs("results")

    task_set = None
    dependencies = None

    # Initalise values for arguments
    if args.t == None and args.u == None:
        print("Please specify either number of tasks, or system utiilisation value.")
        return 0

    # if args.f == None:
    #     print("Please input system configuration")
    #     return 0

    if args.g == None:
        print("Please specify optimisation goal")
        return 0

    if args.g != "c" and args.g != "e2e":
        print("Please select valid optimisation goal (c or e2e)")
        return 0

    if args.d == None:
        args.d = args.t * (args.t - 1) / 2

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

    sys_config = sys_config_generator.generate_sys_config(
        args.c, args.dev, args.p, args.n
    )

    if args.t > 0:
        task_set = task_generator.generate_with_task_limit(
            args.t, args.o, args.e, args.du
        )

    if args.d > 1:
        dependencies = dependency_generator.generate_dependencies(args.d, task_set)

    system = utilities.prepare_system(sys_config, task_set, dependencies)

    tasks_instances, result, hyperperiod = ilp_multicore.multicore_core_scheduler(
        system, args.g
    )

    counter, system = utilities.save_system(system, tasks_instances)
    utilities.save_result(result, counter, system, args.g, hyperperiod)


if __name__ == "__main__":
    main()
