import random


class SystemConfigGenerator:
    def __init__(self):
        pass

    def generate_sys_config(self, num_cores, num_devs, max_prot, max_net):
        cores = []
        devices = []
        network_delays = []

        for i in range(num_devs):
            devices.append(self.generate_device(i, max_prot))

        for i in range(num_cores):
            cores.append(self.generate_core(i, devices))

        for source_index in range(len(devices)):
            for dest_index in range(len(devices)):
                source_dev = devices[source_index]
                dest_dev = devices[dest_index]

                network_delays.append(self.generate_net_delay(source_dev, dest_dev, max_net))

        return {
            "CoreStore": cores,
            "DeviceStore": devices,
            "NetworkDelayStore": network_delays
        }


    def generate_device(self, index, max_prot):
        wcdt = random.randint(0, max_prot)

        return {
            "name": f"d{index + 1}",
            "sppedup": 1,
            "delays": [
                {
                    "protocol": "tcp",
                    "acdt": wcdt,
                    "bcdt": wcdt,
                    "wcdt": wcdt,
                    "distribution": "Normal",
                }
            ],
        }

    def generate_core(self, index, devices):
        dev_index = random.randint(0, len(devices) - 1)

        return {
            "name": f"c{index + 1}",
            "speedup": 1,
            "device": devices[dev_index]["name"],
        }
    
    def generate_net_delay(self, source, dest, max_net):
        wcdt = random.randint(0, max_net)

        return {
            "name": f'{source['name']}-to-{dest['name']}',
            "source": source['name'],
            "dest": dest['name'],
            "acdt": wcdt,
            "bcdt": wcdt,
            "wcdt": wcdt,
            "distribution": "Normal"
        }