import os

import nox

# Global configurations for Nox
# This tells Nox to use 'uv' by default to create venvs and install dependencies
nox.options.default_venv_backend = "uv"
nox.options.sessions = ["tests"]

@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15"])
@nox.parametrize("resolution", ["highest", "lowest"])
def tests(session, resolution):
    """Run test suite across Python versions and dependency resolutions."""

    # Get environment so we write results and coverage to different files
    ci_env = os.getenv("CI_ENV", "local")
    session.run("echo", "Running", "on", f"{ci_env=}")

    # Print actual python version being used
    session.run("python", "--version")

    # Install deps
    session.run("uv", "sync", "--dev", f"--python={session.python}", f"--resolution={resolution}")

    # Run test suite
    session.run("uv", "run", "coverage", "run",
                f'--data-file=.coverage.{ci_env}-{session.python}-{resolution}',
                "-m", "pytest",
                f'--junit-xml=results-{ci_env}-{session.python}-{resolution}.xml')
