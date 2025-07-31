# Generic toolchain interface presented to the rest of the FVM framework. It
# imports different toolchain modules present in this same directory, which
# define the supported FVM methodology steps

import os
import importlib

# To add a toolchain, add it to this list and create a file with the same name
# and .py extension in the toolchains folder
toolchains = ['questa', 'sby']
default_toolchain = 'questa'

default_flags = {}

def get_toolchain():
    """Get the toolchain from a specific environment variable. In the future,
    if the environment variable is not set, we plan to auto-detect which tools
    are available in the PATH and assign the first we find (with some
    priority)"""
    toolchain = os.getenv('FVM_TOOLCHAIN', default_toolchain)
    return toolchain

def get_default_flags(toolchain):
    """Returns sensible tool flags for a specific toolchain"""
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    default_flags = module.default_flags
    print(f'***** {module=}')
    print(f'***** {default_flags=}')
    return default_flags

def define_steps(steps, toolchain):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.define_steps(steps)

def set_timeout(framework, toolchain, step, timeout):
    module = importlib.import_module(f'fvm.toolchains.{toolchain}')
    module.set_timeout(framework, step, timeout)


## TODO: Decide where to put this function
from rich.table import Table
from rich.console import Console

def show_step_summary(step_summary, error, warning, inconclusive=None, proven=None,
                      outdir=None, step=None):
    """
    Displays a table with the step summary.

    Parameters:
        step_summary: dict with the data summary:
            {
                "Violation": {"count": 2, "checks": {...}},
                "Caution": {"count": 1, "checks": {...}},
                ...
            }
        error: category name used as 'Error' row (e.g., 'Violation')
        warning: category name used as 'Warning' row (e.g., 'Caution')
        inconclusive: category name used as 'Inconclusive' row (optional)
        proven: category name used as 'Proven' row (optional)
        outdir: directory where the HTML file will be saved
        step: name of the step
    """
    step_summary_console = Console(force_terminal=True, force_interactive=False,
                                    record=True)

    categories = {
        f"{error}": error,
        f"{warning}": warning,
    }

    if inconclusive:
        categories[f"{inconclusive}"] = inconclusive
    if proven:
        categories[f"{proven}"] = proven

    row_colors = {
        f"{error}": "red",
        f"{warning}": "yellow",
        f"{inconclusive}": "white",
        f"{proven}": "green"
    }

    # Check if at least one row has checks
    show_checks = any(
        step_summary.get(cat, {}).get("checks")
        for cat in categories.values()
    )

    table = Table(title=f"[cyan]{step} summary[/cyan]")
    table.add_column("Severity", style="bold", justify="left")
    table.add_column("Count", style="bold", justify="right")
    if show_checks:
        table.add_column("Checks", style="bold", justify="left")

    # Add rows
    for label, category_name in categories.items():
        data = step_summary.get(category_name, {"count": 0, "checks": {}})
        count = data.get("count", 0)
        checks = data.get("checks", {})

        # Skip optional rows with 0 count
        if label in [f"{inconclusive}", f"{proven}"] and count == 0:
            continue

        # Row color: green if count is 0 for Error/Warning
        if label in [f"{error}", f"{warning}"] and count == 0:
            color = "green"
        else:
            color = row_colors[label]

        if show_checks:
            if checks:
                checks_str = "\n".join([f"{k}: {v}" for k, v in checks.items()])
            else:
                checks_str = "-"
            table.add_row(
                f"[{color}]{label}[/{color}]",
                f"[{color}]{count}[/{color}]",
                f"[{color}]{checks_str}[/{color}]"
            )
        else:
            table.add_row(
                f"[{color}]{label}[/{color}]",
                f"[{color}]{count}[/{color}]"
            )

    step_summary_console.print(table)
    step_summary_console.save_html(f"{outdir}/{step}_summary.html")