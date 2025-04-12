import os
import json
import argparse
from utilities import Utilities
from random_generators.task_set_generator import TaskSetGenerator
from random_generators.dependency_set_generator import DependencySetGenerator


def main():
    parser = argparse.ArgumentParser()
    utilities = Utilities()
    task_generator = TaskSetGenerator()
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
    parser.add_argument('-e', type=float)
    # Maximum duration value
    parser.add_argument('-b', type=float)
    # System config import
    parser.add_argument("-f", type=str, default="")

    args = parser.parse_args()
    del parser

    if (not os.path.exists('output')):
        os.makedirs('output')

    task_set = None
    dependencies = None

    if args.t == None and args.u == None:
        print("Please specify either number of tasks, or system utiilisation value.")
        return 0
    
    if len(args.f) == 0:
        print("Please input system configuration")
        return 0
    
    if args.d == None:
        args.d = args.t * (args.t - 1) / 2

    if args.o == None:
        args.o = 2000000
    else:
        args.o = utilities.MsToNs(args.o)

    if args.e == None:
        args.e = 4000000
    else:
        args.e = utilities.MsToNs(args.o)

    if args.b == None:
        args.b = 8000000
    else:
        args.b = utilities.MsToNs(args.b)

    if args.t > 0:
        task_set = task_generator.generate_with_task_limit(args.t, args.o, args.e, args.b)

    if args.d > 1:
        dependencies = dependency_generator.generate_dependencies(args.d, task_set)

    f = open(args.f)
    system = json.load(f)

    system = {
        "EntityStore": task_set,
        "DependencyStore": dependencies
    }
    
    utilities.save_system(system)

if __name__ == '__main__':
    main()
