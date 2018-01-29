from typing import List

class Job:
    def __init__(self, file_path: str, virtual_paths: List[str]):
        self.__file_path = file_path
        self.__virtual_paths = virtual_paths

    def run(self):
        pass
