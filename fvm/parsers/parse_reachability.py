"""Parsers for reachability reports."""
import re

def parse_single_table(html):
    """Parses a single coverage table from HTML and returns structured data."""
    row_pattern = re.compile(r"<tr.*?>(.*?)</tr>", re.DOTALL)
    cell_pattern = re.compile(r"<t[dh].*?>(.*?)</t[dh]>", re.DOTALL)

    rows = row_pattern.findall(html)
    if not rows:
        return {"title": "Formal Coverage Summary", "data": []}

    headers = [re.sub(r"<.*?>", "", cell).strip() for cell in cell_pattern.findall(rows[0])]
    data = []

    for row in rows[1:]:
        cells = [re.sub(r"<.*?>", "", cell).strip() for cell in cell_pattern.findall(row)]
        data.append({headers[i]: cells[i] for i in range(len(cells))})

    return {"title": "Formal Coverage Summary", "data": data}

def add_total_row(table):
    """Adds a total row to the table, summing numerical fields and computing percentages."""

    if not table.get('data'):
        return table

    total_row = {key: 0 for key in table['data'][0].keys()
                 if key not in ['Coverage Type', 'Unreachable']}
    total_covered = 0
    total_possible = 0

    for row in table['data']:
        for key in total_row:
            try:
                total_row[key] += int(row[key])
            except ValueError:
                pass

        # Extract Unreachable values
        match = re.search(r'(\d+)', row['Unreachable'])
        if match:
            unreachable_value = int(match.group())
            total_covered += unreachable_value

        # Compute total possible cases (Active)
        active_value = int(row.get('Active', 0))
        total_possible += active_value

    # Calculate total Unreachable percentage
    total_percentage = (total_covered / total_possible * 100) if total_possible > 0 else 0
    total_row['Coverage Type'] = 'Total'
    total_row['Unreachable'] = f"{total_covered} ({total_percentage:.1f}%)"

    table['data'].append(total_row)
    return table

def unified_format_table(table, goal=90.0):
    """Converts the table into a unified format."""

    cleaned = []
    for row in table['data']:
        new_row = {}
        for k, v in row.items():

            if isinstance(v, str) and '(' in v and ')' in v:
                match = re.search(r'\(\s*(.*?)\s*\)', v)
                if match:
                    new_row[k] = v.split('(')[0].strip()
                    new_row['Percentage'] = match.group(1)
                    continue
            new_row[k] = v
        if 'Percentage' not in new_row:
            new_row['Percentage'] = 'N/A'
        cleaned.append(new_row)

    new_cleaned = []
    for row in cleaned:
        new_row = {}
        new_row['Coverage Type'] = row['Coverage Type']
        new_row['Total'] = int(row['Active'])
        new_row['Unreachable'] = int(row['Unreachable'])
        new_row['Inconclusive'] = int(row['Inconclusive'])
        new_row['Reachable'] = int(row['Witness'])

        if new_row['Total'] > 0:
            new_row['Percentage'] = f"{new_row['Reachable'] / new_row['Total'] * 100:.1f}%"
        else:
            new_row['Percentage'] = "N/A"

        new_cleaned.append(new_row)

    for row in new_cleaned:
        perc_str = row['Percentage']
        if perc_str == "N/A":
            row['Status'] = "omit"
        else:
            perc_value = float(perc_str.strip('%'))
            row['Status'] = "pass" if perc_value >= goal else "fail"
        row['Goal'] = f"{goal:.1f}%"

    final_data = []
    for row in new_cleaned:
        new_row = {
            "Status": row["Status"],
            "Coverage Type": row["Coverage Type"],
            "Total": row["Total"],
            "Unreachable": row["Unreachable"],
            "Inconclusive": row["Inconclusive"],
            "Reachable": row["Reachable"],
            "Percentage": row["Percentage"],
            "Goal": row["Goal"]
        }
        final_data.append(new_row)

    return final_data
