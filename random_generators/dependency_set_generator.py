import random

class DependencySetGenerator():
    def __init__(self):
        pass

    def generate_dependencies(self, num_dependencies, task_set):
        dependencies = []
        seen = set()

        while (len(dependencies) < num_dependencies):
            source_index = random.randint(0, len(task_set) - 1)
            dest_index = source_index

            while (source_index == dest_index):
                dest_index = random.randint(0, len(task_set) - 1)

            key = (source_index, dest_index)

            if key not in seen:
                seen.add(key)

                dependency = self.format_dependency(source_index, dest_index, task_set)
                dependencies.append(dependency)
            
        return dependencies

    def format_dependency(self, source_index, dest_index, task_set):
        return {
            'name': f't{source_index + 1}-t{dest_index + 1}',
            'source': {
                'port': 'out1',
                'task': task_set[source_index]['name']
            },
            'destination': {
                'port': 'in1',
                'task': task_set[dest_index]['name']
            }
        }