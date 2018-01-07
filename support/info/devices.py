from queue import Queue
from support.devices.control import types
import json


class info():
    def __init__(self, info_controller, dbconnector, queue, device_list):
        self._device_list = device_list
        self.__info_controller = info_controller
        self.__dbconnector = dbconnector
        self.__queue = queue

        self._info_controls = [types.type_generic('devices', get_endpoint=self.get_devices, query_only=True)]

        for info_control in self._info_controls:
            self.__info_controller.append_control(info_control)

    def __wraper(self, function, *args, **kwargs):
        return_queue = Queue()
        self.__queue.put((return_queue, function, args, kwargs))
        results = return_queue.get()
        return results
    def _append_list_device(self, device_list, target_device, device_object):
        new_list = list(device_list)
        found = False
        for x, device_type in enumerate(device_list):
            if device_type['type'] == target_device:
                found = True
                old_device_list = new_list[x]
                old_device_list['devices'].append(device_object)
                new_list[x] = old_device_list
        if not found:
            devices = {'type': target_device,
             'devices': list()}
            devices['devices'].append(device_object)
            new_list.append(devices)
        return new_list
    def get_devices(self):
        devices = self.__wraper(self.__dbconnector.get_devices)
        out_list = list()
        for device in devices:
            for active_device in self._device_list:
                if active_device.device_id == device[3]:
                    device_object = {
                        'id' : device[3],
                        'name' : device[0],
                        'location' : device[1],
                        'controls' : active_device.get_controls()
                    }
                    out_list = self._append_list_device(out_list, active_device.device_type, device_object)
        out_json = json.dumps(out_list)
        return out_json
