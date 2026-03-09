import random
from collections import defaultdict


class DependencySetGenerator:
    def __init__(self):
        pass

    def generate_dependencies(self, num_dependencies, task_set):
        n = len(task_set)

        if n < 2:
            return []

        possible_edges = [(i, j) for i in range(n) for j in range(i + 1, n)]

        num_dependencies = min(num_dependencies, len(possible_edges))

        selected = random.sample(possible_edges, num_dependencies)

        dependencies = [
            self.format_dependency(src, dst, task_set) for src, dst in selected
        ]

        return dependencies

    def format_dependency(self, source_index, dest_index, task_set):
        return {
            "name": f"t{source_index + 1}-t{dest_index + 1}",
            "source": {"port": "out1", "task": task_set[source_index]["name"]},
            "destination": {"port": "in1", "task": task_set[dest_index]["name"]},
        }

    def event_chain_generator(self, dependencies, task_set):

        if len(task_set) < 3:
            return []

        graph = defaultdict(list)
        task_map = {t["name"]: t for t in task_set}

        for dependency in dependencies:
            src = dependency["source"]["task"]
            dst = dependency["destination"]["task"]
            graph[src].append(dst)

        chains = []
        max_depth = len(task_set)

        for task_name in task_map.keys():
            self.find_event_chains(graph, task_name, [], chains, max_depth)

        # keep chains with ≥3 tasks (i.e., ≥2 edges)
        unique = []
        for chain in chains:
            if len(chain) >= 2 and chain not in unique:
                unique.append(chain)

        return unique

    def find_event_chains(self, graph, start, path, chains, max_depth):
        path.append(start)

        if len(path) >= 3:
            chain = []
            for i in range(len(path) - 1):
                chain.append({"source": path[i], "dest": path[i + 1]})
            chains.append(chain)

        if len(path) < max_depth:
            for nxt in graph[start]:
                if nxt not in path:
                    self.find_event_chains(graph, nxt, path, chains, max_depth)

        path.pop()
