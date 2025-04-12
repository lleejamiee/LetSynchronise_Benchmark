import os
import argparse
from utilities import Utilities
from random_generators.task_set_generator import TaskSetGenerator
from random_generators.dependency_set_generator import DependencySetGenerator
from ilp.multicore import MultiCoreScheduler


def main():
    parser = argparse.ArgumentParser()
    utilities = Utilities()
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
    # Optimisation method
    parser.add_argument("-m", type=str)

    args = parser.parse_args()
    del parser

    if not os.path.exists("output"):
        os.makedirs("output")

    task_set = None
    dependencies = None

    if args.t == None and args.u == None:
        print("Please specify either number of tasks, or system utiilisation value.")
        return 0

    if args.f == None:
        print("Please input system configuration")
        return 0

    if args.m == None:
        print("Please specify optimisation method")
        return 0

    if args.m != "c" and args.m != "e2e":
        print("Please select valid optimisation method (c or e2e)")
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

    if args.t > 0:
        task_set = task_generator.generate_with_task_limit(
            args.t, args.o, args.e, args.du
        )

    if args.d > 1:
        dependencies = dependency_generator.generate_dependencies(args.d, task_set)

    system = utilities.save_system(args.f, task_set, dependencies)
    ilp_multicore.multicore_core_scheduler(system, args.m)


if __name__ == "__main__":
    main()
