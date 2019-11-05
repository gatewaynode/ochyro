from invoke import task
from invoke import run


@task
def virtualenv():
    run("virtualenv --prompt ')> FLASK <( ' env --python python3.7")
    run("env/bin/pip install -r requirements.txt")
    print("\nVirtualENV Setup Complete.  Now run: source env/bin/activate\n")


@task
def clean():
    run("rm -rvf __pycache__")
    run("rm -rvf app/__pycache__")
