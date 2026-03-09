# From https://github.com/tu-dortmund-ls12-rt/end-to-end/blob/master/utilities/generator_UUNIFAST.py

from .task_set_generator import TaskSetGenerator
import numpy as np
import random

task_set_generator = TaskSetGenerator()


class UUNIFASTGenerator:
    def __init__(self):
        self.periods = [
            1000000,
            2000000,
            5000000,
            10000000,
            20000000,
            # 50000000,
            # 100000000,
            # 200000000,
            # 500000000,
            # 1000000000,
        ]

    def gen_taskset(
        self,
        num_tasks,
        min_period,
        max_period,
        max_initial_offset,
        utilization,
    ):
        """Generate task sets.

        Variables:
        num_tasks: number of tasks per set
        min_period: minimal period
        max_period: maximal period
        utilization: desired utilization
        """
        # Create utilizations.
        taskset_utilizations = self.generate_utilizations_uniform(
            num_tasks, utilization
        )
        # Create tasksets by matching both of the above.
        taskset = []

        for i in range(num_tasks):
            period = self.periods[random.randint(0, len(self.periods) - 1)]
            initial_offset = random.randint(0, max_initial_offset)
            wcet = int(period * taskset_utilizations[i])
            duration = random.randint(wcet, period)

            taskset.append(
                task_set_generator.format_task(
                    i, period, duration, initial_offset, wcet
                )
            )

        return taskset

    def generate_utilizations_uniform(self, num_tasks, utilization):
        """Generate utilizations with UUNIFAST.

        Variables:
        num_tasks: number of tasks per set
        utilization: desired utilization in (0,1]
        """

        def uunifast(num_tasks, utilization):
            """UUNIFAST utilization pulling."""
            utilizations = []

            if num_tasks == 1:
                utilizations.append(min(utilization, 1))
            else:
                cumulative_utilization = utilization
                for i in range(1, num_tasks):
                    # Randomly set next utilization.
                    cumulative_utilization_next = max(
                        (
                            cumulative_utilization
                            * random.random() ** (1.0 / (num_tasks - i))
                        ),
                        cumulative_utilization - 1,
                    )
                    utilizations.append(
                        cumulative_utilization - cumulative_utilization_next
                    )
                    # Compute remaining utilization.
                    cumulative_utilization = cumulative_utilization_next
                utilizations.append(min(cumulative_utilization_next, 1))
            # Return list of utilizations.

            return utilizations

        # Return one list of utilizations for each task set.
        return uunifast(num_tasks, utilization)
