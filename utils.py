import json, datetime
from threading import Event, Thread
import time

class RepeatedTimer:

    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()

class Response:
    def __init__(self, deadlines):
        self.deadlines = deadlines

    def __repr__(self):
        if len(self.deadlines) == 0:
            return "[]"

        formatted_deadline = datetime.datetime.fromtimestamp(self.deadlines[0]["deadline"]).strftime("%d/%m/%y")

        response = "[\n  (Title: {0}\n   ID: {1}\n   Deadline: {2})".format(self.deadlines[0]["title"],
                                                                            self.deadlines[0]["id"],
                                                                            formatted_deadline)

        for i in range(1, len(self.deadlines)):
            formatted_deadline = datetime.datetime.fromtimestamp(self.deadlines[i]["deadline"]).strftime("%d/%m/%y")
            response += ",\n  (Title: {0}\n   ID: {1}\n   Deadline: {2})".format(self.deadlines[i]["title"],
                                                                                 self.deadlines[i]["id"],
                                                                                 formatted_deadline)

        response += "\n]"

        return response

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)
