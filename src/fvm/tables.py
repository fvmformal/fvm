"""Functions to display tables in the console and save them as HTML and text files."""
import os

from rich.table import Table
from rich.console import Console

def show_step_summary(step_summary, error, warning, inconclusive=None, proven=None,
                      outdir=None, step=None):
    """
    Displays a table with the step summary.

    :param step_summary: dict with the data summary

        Example structure::

            {
                "Violation": {"count": 2, "checks": {...}},
                "Caution": {"count": 1, "checks": {...}},
                ...
            }

    :type step_summary: dict
    :param error: category name used as 'Error' row (e.g., 'Violation')
    :type error: str
    :param warning: category name used as 'Warning' row (e.g., 'Caution')
    :type warning: str
    :param inconclusive: category name used as 'Inconclusive' row (optional)
    :type inconclusive: str or None
    :param proven: category name used as 'Proven' row (optional)
    :type proven: str or None
    :param outdir: directory where the HTML file will be saved
    :type outdir: str or None
    :param step: name of the step
    :type step: str or None
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
    html_file = os.path.join(outdir, f"{step}_summary.html")
    text_file = os.path.join(outdir, f"{step}_summary.txt")
    step_summary_console.save_html(html_file, clear=False)
    step_summary_console.save_text(text_file)

def show_friendliness_score(score, outdir=None, step=None):
    """
    Displays the friendliness score in a table format.

    :param score: friendliness score as a float (0 to 100)
    :type score: float
    :param outdir: directory where the HTML file will be saved
    :type outdir: str or None
    :param step: name of the step
    :type step: str or None
    """

    friendliness_console = Console(force_terminal=True, force_interactive=False,
                                record=True)

    table = Table(show_header=True)
    table.add_column("Friendliness", justify="center")
    table.add_row(f"{score:.2f}%", style="bold green")

    friendliness_console.print(table)
    html_file = os.path.join(outdir, f"{step}_summary.html")
    text_file = os.path.join(outdir, f"{step}_summary.txt")
    friendliness_console.save_html(html_file, clear=False)
    friendliness_console.save_text(text_file)

def show_coverage_summary(data, title="xxx", outdir=None, step=None):
    """
    Displays a table with the coverage summary.

    :param data: list of dicts with the data summary

        Example structure::

            [
                {
                    "Status": "pass" or "fail" or "omit",
                    "Coverage Type": "toggle" or "fsm state" or ...,
                    "Intermediate Column 1": value,
                    ...
                    "Percentage": "85.00%",
                    "Goal": "80.00%"
                },
                ...
            ]

    :type data: list of dicts
    :param title: Title of the table
    :type title: str
    :param outdir: directory where the HTML file will be saved
    :type outdir: str or None
    :param step: name of the step
    :type step: str or None
    """

    console = Console(force_terminal=True, force_interactive=False,
                        record=True)
    table = Table(title=f"[cyan]{title}[/cyan]", show_header=True, header_style="bold")

    if not data:
        return

    # Fixed columns
    table.add_column("Status", justify="center")
    table.add_column("Coverage Type", justify="left", style="cyan")

    # Intermediate columns
    excluded = {"Status", "Coverage Type", "Percentage", "Goal"}
    intermediate_cols = [k for k in data[0].keys() if k not in excluded]
    for col in intermediate_cols:
        table.add_column(col, justify="right")

    # Final columns
    table.add_column("Percentage", justify="right")
    table.add_column("Goal", justify="right")

    for row in data:
        # Color Status and Percentage
        status = row.get("Status", "omit")
        if status == "pass":
            status_str = f"[bold green]{status}[/bold green]"
            perc_str = f"[bold green]{row['Percentage']}[/bold green]"
        elif status == "fail":
            status_str = f"[bold red]{status}[/bold red]"
            perc_str = f"[bold red]{row['Percentage']}[/bold red]"
        else:
            status_str = f"[bold white]{status}[/bold white]"
            perc_str = f"[bold white]{row['Percentage']}[/bold white]"

        # Intermediate column values in order
        intermediate_vals = [str(row[col]) for col in intermediate_cols]

        table.add_row(
            status_str,
            row["Coverage Type"],
            *intermediate_vals,
            perc_str,
            row["Goal"]
        )

    console.print(table)
    html_file = os.path.join(outdir, f"{step}_summary.html")
    text_file = os.path.join(outdir, f"{step}_summary.txt")
    console.save_html(html_file, clear=False)
    console.save_text(text_file)

def show_prove_summary(data, title="Property Summary", outdir=None, step=None):
    """
    Displays a table with the prove summary.

    :param data: dict with the data summary

        Example structure::

            {
                "Proven": {"count": 5, "items": [...]},
                "Vacuous": {"count": 2, "items": [...]},
                "Fired": {"count": 1, "items": [...]},
                ...
            }

    :type data: dict
    :param title: Title of the table
    :type title: str
    :param outdir: directory where the HTML file will be saved
    :type outdir: str or None
    :param step: name of the step
    :type step: str or None
    """

    console = Console(force_terminal=True, force_interactive=False,
                        record=True)
    table = Table(title=f"[cyan]{title}[/cyan]", show_header=True, header_style="bold")

    if not data:
        return

    category_colors = {
        "Proven": "bold green",
        "Vacuous": "bold yellow",
        "Fired": "bold red",
        "Fired with Warning": "bold red",
        "Covered": "bold green",
        "Covered with Warning": "bold yellow",
        "Uncoverable": "bold red",
        "Inconclusive": "bold white"
    }

    has_items = any(info['items'] for cat, info in data.items() if cat not in ["Proven", "Covered"])

    table.add_column("Result", max_width=12)
    table.add_column("Count", justify="right")
    if has_items:
        table.add_column("Names", max_width=50)

    for category, info in data.items():
        count = str(info['count'])
        items = "-"
        if category not in ["Proven", "Covered"] and has_items:
            items = ", ".join(info['items']) if info['items'] else "-"

        style = category_colors.get(category, "")
        if has_items:
            table.add_row(category, count, items, style=style)
        else:
            table.add_row(category, count, style=style)

    console.print(table)
    html_file = os.path.join(outdir, f"{step}_summary.html")
    text_file = os.path.join(outdir, f"{step}_summary.txt")
    console.save_html(html_file, clear=False)
    console.save_text(text_file)
