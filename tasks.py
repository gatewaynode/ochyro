from invoke import task
from invoke import run
import os
from pprint import pprint
import shutil
import logging
import traceback


@task
def virtualenv():
    run("virtualenv --prompt ')> Ochyro <( ' env --python python3.8")
    run("env/bin/pip install -r requirements.txt")
    print("\nVirtualENV Setup Complete.  Now run: source env/bin/activate\n")


@task
def clean():
    run("rm -rvf __pycache__")
    run("rm -rvf app/__pycache__")


@task
def pub():
    # Re-thinking this approach
    pass
