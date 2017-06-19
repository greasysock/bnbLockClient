import requests

class Connect():
    def __init__(self, device_id):
        self.__device_id = device_id
        self.__site = 'http://127.0.0.1:8083/ZWaveAPI/'
    def __url_build(self, url):
        return self.__site + url
    def get_status(self):
        site = self.__url_build('status')
        r = requests.get(site)
        print(r.json())
    def put_code(self, user_code):
        site = self.__url_build('Run/devices[2].instances[0].commandClasses[99].Set(1,{},1)'.format(user_code))
        r = requests.put(site)
        print(r.status_code)
        print(r.json())