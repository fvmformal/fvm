import json
import re

def parse_coverage_table(html):
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
    filtered = [t for t in tables if t['title'].startswith('Formal Coverage Summary for Design')]
    return filtered if filtered else [tables[0]] if tables else []

def add_total_field(table):
    total_row = {key: 0 for key in table['data'][0].keys() if key not in ['Coverage Type', 'Covered (P)']}
    total_covered = 0
    total_possible = 0

    for row in table['data']:
        for key in total_row:
            try:
                total_row[key] += int(re.search(r'\d+', row[key]).group()) if re.search(r'\d+', row[key]) else 0
            except ValueError:
                pass

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


def print_table(table):
    headers = list(table['data'][0].keys())
    col_widths = {h: max(len(h), max(len(str(row[h])) for row in table['data'])) for h in headers}

    print(f"\n{table['title']}\n")
    print(" | ".join(f"{h:{col_widths[h]}}" for h in headers))
    print("-" * (sum(col_widths.values()) + 3 * (len(headers) - 1)))

    for row in table['data']:
        print(" | ".join(f"{str(row[h]):{col_widths[h]}}" for h in headers))