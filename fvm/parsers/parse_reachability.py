import re

def parse_single_table(html):
    """Parses a single coverage table from HTML and returns structured data."""
    row_pattern = re.compile(r"<tr.*?>(.*?)</tr>", re.DOTALL)
    cell_pattern = re.compile(r"<t[dh].*?>(.*?)</t[dh]>", re.DOTALL)

    rows = row_pattern.findall(html)
    headers = [re.sub(r"<.*?>", "", cell).strip() for cell in cell_pattern.findall(rows[0])]
    data = []

    for row in rows[1:]:
        cells = [re.sub(r"<.*?>", "", cell).strip() for cell in cell_pattern.findall(row)]
        data.append({headers[i]: cells[i] for i in range(len(cells))})

    return {"title": "Formal Coverage Summary", "data": data}

def add_total_row(table):
    """Adds a total row to the table, summing numerical fields and computing percentages."""
    total_row = {key: 0 for key in table['data'][0].keys() if key not in ['Coverage Type', 'Unreachable']}
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

def print_table(table):
    """Prints the table in a well-formatted manner."""
    headers = table['data'][0].keys()
    col_widths = {header: max(len(header), max(len(str(row[header])) for row in table['data'])) for header in headers}

    def format_row(row):
        return " | ".join(str(row[h]).ljust(col_widths[h]) for h in headers)

    print(f"\n{table['title']}\n")
    print(format_row({h: h for h in headers}))
    print("-" * sum(col_widths.values()) + "-" * (len(headers) * 3))
    
    for row in table['data']:
        print(format_row(row))