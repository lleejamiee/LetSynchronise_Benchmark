import math
from pulp import GUROBI, LpProblem, LpMinimize, LpVariable, lpSum
from gurobipy import GRB


class MultiCoreScheduler:
    def __init__(self):
        self.devices = None
        self.cores = None
        self.network_delays = None

        self.task_data = None
        self.tasks_instances = None

        self.assigned_vars = None
        self.exec_start_vars = None
        self.exec_end_vars = None

    def multicore_core_scheduler(self, system, method, fixed_timings=False):
        prob = LpProblem("Multicore_Core_Scheduling", LpMinimize)

        self.devices = system["DeviceStore"]
        self.cores = system["CoreStore"]
        self.network_delays = system["NetworkDelayStore"]

        tasks = system["EntityStore"]
        dependencies = system["DependencyStore"]
        self.task_data = self.format_tasks(tasks, dependencies)

        makespan = self.calculate_makespan(tasks)

        N = self.calculate_largeN(tasks)

        self.tasks_instances = self.create_task_instances(makespan, tasks, N)

        # Variables
        # Variable for task instances, and their core assignment
        self.assigned_vars = LpVariable.dicts(
            "assigned",
            (
                (task["name"], core["name"])
                for task in self.tasks_instances
                for core in self.cores
            ),
            lowBound=0,
            upBound=1,
            cat="Binary",
        )

        # Variable for execution start time for each instance. (s_(i,j))
        self.exec_start_vars = LpVariable.dicts(
            "start",
            (
                (task["name"], instance["instance"])
                for task in self.tasks_instances
                for instance in task["value"]
            ),
            lowBound=0,
            cat="Integer",
        )

        # Variable for execution end time for each instance. (e_(i,j))
        self.exec_end_vars = LpVariable.dicts(
            "end",
            (
                (task["name"], instance["instance"])
                for task in self.tasks_instances
                for instance in task["value"]
            ),
            lowBound=0,
            cat="Integer",
        )

        # ψ_(x,k,y,l)^core
        psi_task_core_vars = LpVariable.dicts(
            "psi_task_core",
            [
                (task1["name"], core1["name"], task2["name"], core2["name"])
                for core1 in self.cores
                for core2 in self.cores
                for task1 in self.tasks_instances
                for task2 in self.tasks_instances
                if task1 != task2
            ],
            lowBound=0,
            upBound=1,
            cat="Binary",
        )

        # ψ_(x,y)^core
        # The matrices are symmetrical, which is why only the half of it is being considered for optimisation purposes.
        psi_tasks_vars = LpVariable.dicts(
            "psi_tasks",
            [
                (task1["name"], task2["name"])
                for task1 in self.tasks_instances
                for task2 in self.tasks_instances
                if task1 != task2
            ],
            lowBound=0,
            upBound=1,
            cat="Binary",
        )

        # b_(x,i,y,j)^task
        bool_task_vars = LpVariable.dicts(
            "bool_task",
            [
                (task1["name"], value1["instance"], task2["name"], value2["instance"])
                for task1 in self.tasks_instances
                for task2 in self.tasks_instances
                if task1 != task2
                for value1 in task1["value"]
                for value2 in task2["value"]
            ],
            lowBound=0,
            upBound=1,
            cat="Binary",
        )

        # Variable to track if a core is being used (u_j)
        core_used_vars = LpVariable.dicts(
            "u", ((core["name"]) for core in self.cores), lowBound=0, upBound=1, cat="Binary"
        )
        cores_used_var = LpVariable("cores_used", cat="Integer")

        # lambda_(x,y)
        lambda_vars = LpVariable.dicts(
            "lambda",
            [
                (task1["name"], task2["name"])
                for task1 in self.tasks_instances
                for task2 in self.tasks_instances
                if task1 != task2
            ],
            lowBound=0,
            cat="Integer",
        )

        if method == "e2e":
            # b_(x,i,y,j)^dep
            bool_dep_vars = LpVariable.dicts(
                "bool_dep",
                [
                    (
                        task1["name"],
                        value1["instance"],
                        task2["name"],
                        value2["instance"],
                    )
                    for task1 in self.tasks_instances
                    for task2 in self.tasks_instances
                    if task1 != task2
                    for value1 in task1["value"]
                    for value2 in task2["value"]
                ],
                lowBound=0,
                upBound=1,
                cat="Binary",
            )

            delay_vars = LpVariable.dicts(
                "delay",
                [
                    (
                        task1["name"],
                        value1["instance"],
                        task2["name"],
                        value2["instance"],
                    )
                    for task1 in self.tasks_instances
                    for task2 in self.tasks_instances
                    if task1 != task2
                    for value1 in task1["value"]
                    for value2 in task2["value"]
                ],
                lowBound=0,
                cat="Integer",
            )
            total_delay_var = LpVariable("total_delay", cat="Integer")

        # Constraint
        # 1. A task instance can have exactly one core assigned to it. (From C1 - C17)
        for task in self.tasks_instances:
            prob += (
                lpSum(
                    self.assigned_vars[(task["name"], core["name"])]
                    for core in self.cores
                )
                == 1
            )
        
        # Restrict cores or devices if required
        for task in self.tasks_instances:
            requiredCore = self.get_task_data(task["name"])["requiredCore"]
            requiredDevice = self.get_task_data(task["name"])["requiredDevice"]

            if requiredCore != None:
                prob += self.assigned_vars[(task["name"], requiredCore)] == 1

            if requiredDevice != None:
                prob += lpSum(
                    self.assigned_vars[(task["name"], core["name"])]
                    for core in cores
                    if core["device"] == requiredDevice
                ) == 1
            


        # 2b. A task' total execution time must be equal to the specified execution time. (From C49 - C82)
        # 2c. A task's execution start time must be greater than or equal to its LET start time,
        # 2d. A task's execution end time must be less than or equal to its LET end time. (From C83 - C150)
        for task in self.tasks_instances:
            wcet = self.get_task_data(task["name"])["wcet"]
            for instance in filter(lambda x: x["instance"] != -1, task["value"]):
                instance_name = (task["name"], instance["instance"])
                prob += (
                    self.exec_end_vars[instance_name]
                    - self.exec_start_vars[instance_name]
                    == wcet
                )
                prob += self.exec_start_vars[instance_name] >= instance["letStartTime"]
                prob += self.exec_end_vars[instance_name] <= instance["letEndTime"]

                # If timings have been pre-determined, constrain them here
                if fixed_timings and "EntityInstancesStore" in system:
                    task_value = next((x for x in system["EntityInstancesStore"] if x["name"] == task["name"]), None)
                    if task_value != None:
                        instance_value = next((x for x in task_value["value"] if x["instance"] == instance["instance"]), None)
                        if instance_value != None:
                            prob += self.exec_start_vars[instance_name] == instance_value["executionIntervals"][0]["startTime"]
                            prob += self.exec_end_vars[instance_name] == instance_value["executionIntervals"][0]["endTime"]


        # 3a. Execution intervals for the task instances on the same core should not overlap. (From C151 - C790)
        for core1 in self.cores:
            for core2 in self.cores:
                for task1 in self.tasks_instances:
                    for task2 in self.tasks_instances:
                        if task1 != task2:
                            task_x = task1["name"], core1["name"]
                            task_y = task2["name"], core2["name"]
                            task_pair = task_x + task_y

                            prob += (
                                psi_task_core_vars[task_pair]
                                <= self.assigned_vars[task_x]
                            )
                            prob += (
                                psi_task_core_vars[task_pair]
                                <= self.assigned_vars[task_y]
                            )
                            prob += (
                                psi_task_core_vars[task_pair]
                                >= self.assigned_vars[task_x]
                                + self.assigned_vars[task_y]
                                - 1
                            )

        # 3b. (From C701 - C950)
        for task1 in self.tasks_instances:
            for task2 in self.tasks_instances:
                if task1 != task2:
                    task_pair = (task1["name"], task2["name"])

                    prob += psi_tasks_vars[task_pair] == lpSum(
                        psi_task_core_vars[
                            task1["name"], core1["name"], task2["name"], core2["name"]
                        ]
                        for core1 in self.cores
                        for core2 in self.cores
                        if core1 != core2
                    )

        # 3c, 3d. (From C951 - C1110)
        for task1 in self.tasks_instances:
            for task2 in self.tasks_instances:
                if task1 != task2:
                    for instance1 in filter(
                        lambda x: x["instance"] != -1, task1["value"]
                    ):
                        for instance2 in filter(
                            lambda x: x["instance"] != -1, task2["value"]
                        ):
                            task_x = (task1["name"], instance1["instance"])
                            task_y = (task2["name"], instance2["instance"])
                            instances_pair = task_x + task_y
                            task_pair = (task1["name"], task2["name"])

                            prob += (
                                self.exec_end_vars[task_x]
                                - self.exec_start_vars[task_y]
                                <= N * bool_task_vars[instances_pair]
                                + N * psi_tasks_vars[task_pair]
                            )
                            prob += (
                                self.exec_end_vars[task_y]
                                - self.exec_start_vars[task_x]
                                <= N
                                - N * bool_task_vars[instances_pair]
                                + N * psi_tasks_vars[task_pair]
                            )



        # 5. If a task instance uses a core, the core is marked used
        for core in self.cores:
            prob += core_used_vars[core["name"]] <= lpSum(self.assigned_vars[(task["name"], core["name"])] for task in self.tasks_instances)
            for task in self.tasks_instances:
                prob += core_used_vars[(core["name"])] >= self.assigned_vars[(task["name"], core["name"])]
        

        if method == "e2e":
            # 6a. Transmission latencies between two tasks
            for task1 in self.tasks_instances:
                for task2 in self.tasks_instances:
                    if task1 != task2:
                        task_pair = (task1["name"], task2["name"])
                        prob += lambda_vars[task_pair] == lpSum(
                            psi_task_core_vars[
                                (task1["name"], core1["name"], task2["name"], core2["name"])
                            ]
                            * self.get_delay(core1, core2, N)
                            for core1 in self.cores
                            for core2 in self.cores
                        )

            # 6b. Constraints for task instance dependencies
            for task2 in self.tasks_instances:
                for depends_on in self.get_task_data(task2["name"])["dependsOn"]:
                    for instance2 in filter(
                        lambda x: x["instance"] != -1, task2["value"],
                    ):
                        for instance1 in self.get_instances(depends_on):
                            dep_pair = (depends_on, task2["name"])
                            dep_instances_pair = (
                                depends_on,
                                instance1["instance"],
                                task2["name"],
                                instance2["instance"],
                            )
                            prob += (
                                instance1["letEndTime"]
                                + lambda_vars[dep_pair]
                                - instance2["letStartTime"]
                                <= N - N * bool_dep_vars[dep_instances_pair]
                            )

                        prob += (
                            lpSum(
                                bool_dep_vars[
                                    (
                                        depends_on,
                                        instance1["instance"],
                                        task2["name"],
                                        instance2["instance"],
                                    )
                                ]
                                for instance1 in self.get_instances(depends_on)
                            )
                            == 1
                        )
            
            # 6c. Delay constraints
            for task1 in self.tasks_instances:
                for task2 in self.tasks_instances:
                    if task1 != task2:
                        for instance1 in task1["value"]:
                            for instance2 in filter(
                                lambda x: x["instance"] != -1, task2["value"]
                            ):
                                dep_instances_pair = (
                                    task1["name"],
                                    instance1["instance"],
                                    task2["name"],
                                    instance2["instance"],
                                )
                                prob += (
                                    delay_vars[dep_instances_pair]
                                    >= instance2["letStartTime"]
                                    - instance1["letEndTime"]
                                    - 2*N
                                    + 2*N * bool_dep_vars[dep_instances_pair]
                                )
                                prob += (
                                    delay_vars[dep_instances_pair]
                                    <= instance2["letStartTime"]
                                    - instance1["letEndTime"]
                                    + 2*N
                                    - 2*N * bool_dep_vars[dep_instances_pair]
                                )

            # Set the total delay
            prob += total_delay_var == lpSum(delay_vars)
        
        # Set the number of used cores (total)
        prob += cores_used_var == lpSum(core_used_vars)

        if method == "c":
            prob += cores_used_var, "Minimise Core Usage"
        elif method == "e2e":
            prob += total_delay_var, "Minimise End-to-End Response Time"
        
        prob.solve(GUROBI(timeLimit=5*60))

        self.update_schedule()

        return self.tasks_instances, prob

    def format_tasks(self, tasks, dependencies):
        formatted_tasks = []

        for task in tasks:
            source_tasks = self.get_source_tasks(task, dependencies)
            core = task.get("core", None)
            device = task.get("device", None)

            data = {
                "name": task["name"],
                "offset": task["activationOffset"],
                "duration": task["duration"],
                "period": task["period"],
                "wcet": task["wcet"],
                "requiredCore": core,
                "requiredDevice": device,
                "dependsOn": source_tasks,
            }

            formatted_tasks.append(data)

        return formatted_tasks

    def update_schedule(self):
        for task in self.tasks_instances:
            task["value"] = [
                instance for instance in task["value"] if instance["instance"] != -1
            ]
            for instance in task["value"]:
                for core in self.cores:
                    if self.assigned_vars[(task["name"], core["name"])].varValue == 1:
                        start_time = self.exec_start_vars[
                            (task["name"], instance["instance"])
                        ].varValue
                        end_time = self.exec_end_vars[
                            (task["name"], instance["instance"])
                        ].varValue

                        execution_time = [
                            {
                                "core": core["name"],
                                "endTime": end_time,
                                "startTime": start_time,
                            }
                        ]
                        instance["executionTime"] = self.get_task_data(task["name"])["wcet"]
                        instance["currentCore"] = core
                        instance["executionIntervals"] = execution_time

    def create_task_instances(self, makespan, tasks, N):
        task_instances = []

        for task in tasks:
            instances = []
            number_of_instances = math.ceil(
                (makespan - task["initialOffset"]) / task["period"]
            )

            instances.append(self.create_negative_instance(task, N))

            for i in range(0, number_of_instances):
                instances.append(self.create_task_instance(task, i))

            data = {
                "name": task["name"],
                "type": "task",
                "initialOffset": task["initialOffset"],
                "value": instances,
            }

            task_instances.append(data)

        return task_instances

    def create_negative_instance(self, task, N):
        return {
            "instance": -1,
            "letStartTime": -N,
            "letEndTime": -N + task["duration"],
            "executionTime": task["wcet"],
        }

    def create_task_instance(self, task, index):
        periodStartTime = (index * task["period"]) + task["initialOffset"]
        periodEndTime = periodStartTime + task["period"]
        letStartTime = periodStartTime + task["activationOffset"]
        letEndTime = letStartTime + task["duration"]

        return {
            "instance": index,
            "periodStartTime": periodStartTime,
            "periodEndTime": periodEndTime,
            "letStartTime": letStartTime,
            "letEndTime": letEndTime,
            "executionTime": task["wcet"],
        }

    def get_task_data(self, task_name):
        return next(
            (task for task in self.task_data if task["name"] == task_name)
        )

    def get_device_for_core(self, core):
        return next((c["device"] for c in self.cores if c["name"] == core), None)

    def get_device_delay(self, device_name, protocol):
        for device in self.devices:
            if device["name"] == device_name:
                for delay in device["delays"]:
                    if delay["protocol"] == protocol:
                        return delay
        
        return None

    def get_delay(self, source, dest, N):
        if source["device"] == dest["device"]:
            return 0

        for link in self.network_delays:
            if link["source"] == source["device"] and link["dest"] == dest["device"]:

                comm_delay = (
                    link["wcdt"]
                    + self.get_device_delay(source["device"], "tcp")["wcdt"]
                    + self.get_device_delay(dest["device"], "tcp")["wcdt"]
                )
                return comm_delay

        return N

    def get_instances(self, task_name):
        for task in self.tasks_instances:
            if task["name"] == task_name:
                return task["value"]
        
        return []

    def get_source_tasks(self, task, dependencies):
        source_tasks = []

        if dependencies is not None:
            for dependency in filter(
                lambda x: x["source"]["task"] != "__system"
                and x["destination"]["task"] != "__system",
                dependencies,
            ):
                if dependency["destination"]["task"] == task["name"]:
                    source_tasks.append(dependency["source"]["task"])

        return source_tasks
    

    @staticmethod
    def calculate_hyperperiod(task_set):
        taskPeriods = [task["period"] for task in task_set]
        return math.lcm(*taskPeriods)

    @staticmethod
    def calculate_hyperoffset(task_set):
        taskOffsets = [task["initialOffset"] for task in task_set]
        return max(taskOffsets)

    @staticmethod
    def calculate_makespan(task_set):
        hyperperiod = MultiCoreScheduler.calculate_hyperperiod(task_set)
        hyperoffset = MultiCoreScheduler.calculate_hyperoffset(task_set)
        return hyperperiod * math.ceil((2 * hyperperiod + 2000000) / hyperperiod) + hyperoffset 

    @staticmethod
    def calculate_largeN(task_set):
        makespan = MultiCoreScheduler.calculate_makespan(task_set)
        return makespan * 2