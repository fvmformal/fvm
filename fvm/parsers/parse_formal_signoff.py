"""
Parser for formal signoff reports.

This module provides functions to parse the coverage tables and convert them
into a unified coverage table format.

It is specifically for Questa PropCheck results.
"""
import re

def parse_coverage_table(html):
    """
    Parse formal signoff tables from HTML content.

    :param html: HTML string containing coverage tables.
    :type html: str
    :return: A list of parsed tables with titles and row data.
    :rtype: list[dict[str, list[dict[str, str]]]]
    """
    tables = []

    button_pattern = re.compile(r"<button.*?>(.*?)</button>", re.DOTALL)
    table_pattern = re.compile(r"<table>.*?</table>", re.DOTALL)
    row_pattern = re.compile(r"<tr.*?>(.*?)</tr>", re.DOTALL)
    cell_pattern = re.compile(r"<t[dh].*?>(.*?)</t[dh]>", re.DOTALL)

    buttons = button_pattern.findall(html)
    tables_html = table_pattern.findall(html)

    for title, table_html in zip(buttons, tables_html):
        rows = row_pattern.findall(table_html)
        headers = [re.sub(r"<.*?>", "", cell).strip() for cell in cell_pattern.findall(rows[0])]
        data = []

        for row in rows[1:]:
            cells = [re.sub(r"<.*?>", "", cell).strip() for cell in cell_pattern.findall(row)]
            data.append({headers[i]: cells[i] for i in range(len(cells))})

        tables.append({
            'title': title.strip(),
            'data': data
        })

    return tables

def filter_coverage_tables(tables):
    """
    Filter coverage tables to select only the design summary,
    not the individual module summaries.

    :param tables: List of coverage tables with titles and data.
    :type tables: list[dict]
    :return: Filtered list of coverage tables.
    :rtype: list[dict]
    """
    filtered = [t for t in tables if t['title'].startswith('Formal Coverage Summary for Design')]
    return filtered if filtered else [tables[0]] if tables else []

def add_total_field(table):
    """
    Add a total row to the coverage table

    :param table: A coverage table with parsed row data.
    :type table: dict
    :return: The input table with an additional total row.
    :rtype: dict
    """
    total_row = {key: 0 for key in table['data'][0].keys()
                 if key not in ['Coverage Type', 'Covered (P)']}
    total_covered = 0
    total_possible = 0

    for row in table['data']:
        for key in total_row:
            match = re.search(r'\d+', row[key])
            total_row[key] += int(match.group()) if match else 0
        # Extraer valores de Covered (P)
        covered_match = re.search(r'(\d+)', row['Covered (P)'])
        if covered_match:
            total_covered += int(covered_match.group())

        # Calcular posibles casos (Total - Excluded)
        total_value = int(row.get('Total', 0))
        excluded_value = int(row.get('Excluded', 0)) if 'Excluded' in row else 0
        total_possible += total_value - excluded_value

    # Calcular el porcentaje total
    coverage_percentage = (total_covered / total_possible * 100) if total_possible > 0 else 0
    total_row['Coverage Type'] = 'Total'
    total_row['Covered (P)'] = f"{total_covered} ({coverage_percentage:.1f}%)"

    table['data'].append(total_row)
    return table

def unified_format_table(table, goal=90.0):
    """
    Convert the formal signoff table into the unified coverage table format.

    This function reformats the columns of a coverage summary into a standard
    schema including fields like status, totals, covered values, and
    percentages. The ``goal`` parameter defines the pass/fail threshold.

    :param table: Parsed coverage table.
    :type table: dict
    :param goal: Coverage percentage required to mark a row as "pass".
    :type goal: float, optional
    :return: Reformatted coverage data with unified schema.
    :rtype: list[dict]
    """
    final_data = []

    for row in table["data"]:
        new_row = {}

        new_row["Coverage Type"] = row.get("Coverage Type", "Total")

        total = int(row.get("Total", 0))
        uncovered = int(row.get("Uncovered", 0))
        excluded = int(row.get("Excluded", 0))

        covered = total - uncovered - excluded
        covered = max(covered, 0)

        if total == 0:
            percentage = "N/A"
        else:
            perc_value = (covered / (total - excluded)) * 100 if (total - excluded) > 0 else 0.0
            percentage = f"{perc_value:.1f}%"

        if percentage == "N/A":
            status = "omit"
        else:
            perc_num = float(percentage.strip("%"))
            status = "pass" if perc_num >= goal else "fail"

        new_row.update({
            "Status": status,
            "Total": total,
            "Uncovered": uncovered,
            "Excluded": excluded,
            "Covered": covered,
            "Percentage": percentage,
            "Goal": f"{goal:.1f}%"
        })

        final_data.append(new_row)

    return final_data
