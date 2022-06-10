from __future__ import annotations

import inspect
import threading
import time
from dataclasses import dataclass
from typing import Generator

import requests

__all__ = ['sleep', 'run_async', 'make_async']


@dataclass
class AsyncTask:
    gen: Generator
    locked_by: AsyncTask | None = None
    result = None

    def send(self, value):
        if self.locked_by:
            try:
                result = self.locked_by.send(value)

                if inspect.isgenerator(result):
                    result = AsyncTask(result)
                    self.locked_by.lock_by(result)

            except StopIteration as e:
                self.locked_by = None
                result = e.value
        else:
            try:
                result = self.gen.send(value)
            except TypeError:
                result = self.gen.send(None)

        return result

    def lock_by(self, task: AsyncTask):
        self.locked_by = task


def sleep(secs: float):
    until = time.time() + secs

    while time.time() < until:
        yield


def run_async(*tasks: Generator):
    tasks = [AsyncTask(t) for t in tasks]
    results = []

    while tasks:
        for t in tasks:
            try:
                t.result = t.send(t.result)

                if inspect.isgenerator(t.result):
                    t.result = AsyncTask(t.result)
                    t.lock_by(t.result)

            except StopIteration as e:
                results.append(e.value)
                tasks.remove(t)

    return results


def make_async(func):
    def deco(*args, **kwargs):
        result = []

        def _():
            nonlocal result
            result = func(*args, **kwargs)

        t = threading.Thread(target=_)
        t.start()

        while t.is_alive():
            yield sleep(0)

        return result

    return deco
