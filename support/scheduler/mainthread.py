from threading import Thread
import time
from queue import Queue

#one epoch day is cutoff
current_cutoff = 60 * 60 * 24
#check tasks every 30 seconds
wait_period = 30

class task():
    __time = None
    __call_function = None
    __args = None
    __kwargs = None
    __callback = None
    __success = None
    __fail = 0
    __retry = 3
    @property
    def time(self):
        return self.__time
    @time.setter
    def time(self, value):
        self.__time = value
    @property
    def call_function(self):
        return self.__call_function
    @call_function.setter
    def call_function(self, value):
        self.__call_function = value
    @property
    def args(self):
        return self.__args
    @args.setter
    def args(self, value):
        self.__args = value
    @property
    def kwargs(self):
        return self.__kwargs
    @kwargs.setter
    def kwargs(self, value):
        self.__kwargs = value
    @property
    def callback(self):
        return self.__callback
    @callback.setter
    def callback(self, value):
        self.__callback = value
    @property
    def success(self):
        return self.__success
    @success.setter
    def success(self, value):
        self.__success = value
    def __log_fail(self):
        self.__fail += 1
    def execute(self):
        task_thread = self.task_execution()
        task_thread.start()
        return_queue = Queue()
        if self.__args != None and self.__kwargs == None:
            task_thread.queue.put((return_queue, self.__call_function, self.__args, {}))

        get_return = return_queue.get()
        task_thread.stop()
        if get_return == self.__success:
            try:
                self.__callback()
            except TypeError:
                return True
            return True
        elif get_return != self.__success:
            self.__log_fail()
            if self.__fail >= self.__retry:
                print('Task failed to execute. Removing from task queue')
                return True
            return False
    class task_execution(Thread):
        def __init__(self):
            Thread.__init__(self)
            self.queue = Queue()
        def run(self):
            return_queue, f, args, kwargs = self.queue.get()
            results = f(*args, **kwargs)
            return_queue.put(results)
            self.queue.task_done()
        def stop(self):
            self._stop()

def get_task_start(task):
    return task.time

class interface(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.__current_events = list()
        self.__upcoming_events = list()
        self.__loop_start = int(time.time())
    def run(self):
        self.__start_loop()
    def append_task(self, event_time, function, args=None, kwargs=None, success_condition=True, callback=None):
        print(event_time)
        if event_time <= self.__loop_start + current_cutoff:
            self.__append_task_now(event_time, function, args, kwargs, success_condition, callback)
        elif event_time > self.__loop_start + current_cutoff:
            self.__append_task_later(event_time, function, args, kwargs, success_condition, callback)
    def __append_task_now(self, event_time, function, args, kwargs, success_condition, callback):
        task_obj = task()
        task_obj.time = event_time
        task_obj.call_function = function
        task_obj.args = args
        task_obj.kwargs = kwargs
        task_obj.callback = callback
        task_obj.success = success_condition
        self.__current_events.append(task_obj)
    def __append_task_later(self, event_time, function, args, kwargs, success_condition, callback):
        task_obj = task()
        task_obj.time = event_time
        task_obj.call_function = function
        task_obj.args = args
        task_obj.kwargs = kwargs
        task_obj.callback = callback
        task_obj.success = success_condition
        self.__upcoming_events.append(task_obj)
    def __restart_loop(self):
        self.__loop_start = int(time.time())
        upcoming_events = list(self.__upcoming_events)
        self.__upcoming_events = list()
        for event in upcoming_events:
            self.append_task(event.time, event.call_function, args=event.args, kwargs=event.kwargs, success_condition=event.success, callback=event.callback)
        self.__start_loop()
    def __start_loop(self):
        while True:
            sorted_events = sorted(self.__current_events, key=get_task_start)
            for event in sorted_events:
                if event.time <= int(time.time()):
                    success = event.execute()
                    if success: self.__current_events.remove(event)
                    break
            if int(time.time()) >= self.__loop_start + current_cutoff:
                self.__restart_loop()
                break
            time.sleep(wait_period)