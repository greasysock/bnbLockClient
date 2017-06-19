import requests



class Connect():
    def __init__(self, device_id):
        self.__device_id = device_id
        self.__user = 'admin'
        self.__pass = '091560Cg'
        self.__auth = (self.__user, self.__pass)
        self.__site = 'http://127.0.0.1:8083/ZWaveAPI/'
    def __url_build(self, url):
        return self.__site + url
    def get_status(self):
        site = self.__url_build('status')
        r = requests.get(site)
        print(r.json())
    def put_code(self, user_code):
        site = self.__url_build('Run/devices[2].instances[0].commandClasses[99].Set(1,{},1)'.format(user_code))
        r = requests.put(site, auth=self.__auth)
        print(r.status_code)
        print(r.json())
    def get_code(self, user_id):
        site = self.__url_build('Run/devices[2].instances[0].commandClasses[99].Get({})'.format(user_id))
        r = requests.get(site, auth=self.__auth)