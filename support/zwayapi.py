import requests

class Connect():
    def __init__(self, device_id):
        self.__device_id = device_id
        self.__site = 'http://127.0.0.1:8083/ZAutomation/api/v1/'
    def __url_build(self, url):
        return self.__site + url
    def get_locations(self):
        site = self.__url_build('locations')
        r = requests.get(site)
        print(r.json())
    def get_status(self):
        site = self.__url_build('status')
        r = requests.get(site)
        print(r.json())