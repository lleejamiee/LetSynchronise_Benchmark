import random


class TaskSetGenerator:
    def __init__(self):
        pass

    def generate_with_task_limit(
        self, num_tasks, max_init_offset, max_wcet, max_duration
    ):
        tasks = []
        for i in range(num_tasks):
            tasks.append(self.generate_task(i, max_init_offset, max_wcet, max_duration))

        return tasks

    def generate_task(self, index, max_init_offset, max_wcet, max_duration):
        periods = [
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

        period = periods[random.randint(0, len(periods) - 1)]
        if max_duration > period:
            max_duration = period
        duration = random.randint(1, max_duration)

        initial_offset = random.randint(0, max_init_offset)

        if max_wcet > duration:
            max_wcet = duration
        wcet = random.randint(0, max_wcet)

        return self.format_task(index, period, duration, initial_offset, wcet)

    def format_task(self, index, period, duration, initial_offset, wcet):
        return {
            "name": f"t{index + 1}",
            "type": "task",
            "acet": wcet,
            "bcet": wcet,
            "wcet": wcet,
            "core": None,
            "distribution": "Normal",
            "inputs": ["in1"],
            "outputs": ["out1"],
            "priority": None,
            "activationOffset": 0,
            "initialOffset": initial_offset,
            "period": period,
            "duration": duration,
        }
