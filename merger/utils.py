import random
from subprocess import Popen


def random_between(a: float, b: float) -> float:
    assert b > a
    return a + (b - a) * random.random()

def run_cmd(command: str):
    print(f"Running shell command: {command}")
    Popen(
        command,
        shell=True
    ).wait()
