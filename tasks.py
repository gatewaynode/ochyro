from invoke import task
from invoke import run
import os
from pprint import pprint
import shutil
import logging
import traceback


@task
def virtualenv():
    run("virtualenv --prompt ')> Ochyro <( ' env --python python3.7")
    run("env/bin/pip install -r requirements.txt")
    print("\nVirtualENV Setup Complete.  Now run: source env/bin/activate\n")


@task
def clean():
    run("rm -rvf __pycache__")
    run("rm -rvf app/__pycache__")


@task
def pub():
    # Pre clean the build directory
    build_artifacts = os.listdir(os.path.join("core", "build"))
    print("Found in build dir:")
    pprint(build_artifacts)
    print("Removing local artifacts:")
    for filename in build_artifacts:
        _filename = os.path.join("core", "build", filename)
        if filename not in ["index", "view", "static"]:
            if os.path.isfile(_filename):
                try:
                    print(f"removing file {_filename}")
                    os.remove(_filename)
                except Exception as e:
                    logging.error(traceback.format_exc())
            else:
                try:
                    print(f"removing dir {_filename}")
                    shutil.rmtree(_filename)
                except Exception as e:
                    logging.error(traceback.format_exc())
    # @TODO publish
