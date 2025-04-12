import os
import json


class Utilities:
    def __init__(self):
        pass

    def MsToNs(ms):
        return ms * 1000000

    def save_system(self, sys_config_path, task_set, dependencies):
        f = open(sys_config_path)
        sys_config = json.load(f)

        system = {
            "EntityStore": task_set,
            "DependencyStore": dependencies,
            "CoreStore": sys_config["CoreStore"],
            "DeviceStore": sys_config["DeviceStore"],
            "NetworkDelayStore": sys_config["NetworkDelayStore"],
        }

        directory = "output"
        base_filename = "system"
        extension = ".json"

        counter = 1
        while True:
            file_name = f"{base_filename}{counter:03d}{extension}"

            file_path = os.path.join(directory, file_name)

            if not os.path.exists(file_path):
                break

            counter += 1

        # with open(file_path, "w") as outfile:
        #     json.dump(system, outfile, indent=4)

        return system
