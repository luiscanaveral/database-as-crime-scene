from .common.decorators.singleton import singleton
from .common.logger import log


class Notebook:
    def say_hello(self):
        print("Hello")

    def build_connection_string(self):
        pass

    def setup(self):
        self.build_connection_string()

    def print(self, *args):
        log(args)

    def print_sql(self, multi_line_code):
        log(multi_line_code, log_type="syntax")


@singleton
class DatabaseAsCrimeScene:
    def __init__(self):
        self.data = []

    def setup(self):
        print("Hola")
