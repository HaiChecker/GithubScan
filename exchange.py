from flask import template_rendered
from contextlib import contextmanager


class Exchange:
    def __init__(self):
        self._subscribers = set()

    def attach(self, task):
        self._subscribers.add(task)

    def detach(self, task):
        self._subscribers.remove(task)

    def subscribe(self, tasks):
        if type(tasks) is set:
            for task in tasks:
                self.attach(task)
        else:
            self.attach(tasks)

    def send(self, msg):
        for subscriber in self._subscribers:
            subscriber.send(msg)
