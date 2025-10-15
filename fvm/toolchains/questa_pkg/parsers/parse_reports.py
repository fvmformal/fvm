"""Parsers for coverage reports and convert them to HTML."""
import re

def parse_formal_reachability_report_to_html(input_file, output_file="report.html"):
    """Parses a formal reachability report text file and converts it to an
    HTML file with styling and interactivity."""
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    html_content = []
    assumptions = []
    index_items = []
    tables = []
    current_section = None
    legend = []
    cover_table = False
    cover_type_table = []
    table_title = ""
    report_generated = ""

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("Report Generated :"):
            report_generated = stripped_line
            continue

        if re.search(r"-{2,}", stripped_line):
            continue

        if "Legend" in stripped_line:
            current_section = "Legend"
            legend = []
            continue

        if current_section == "Legend":
            if stripped_line == "":
                current_section = None
            else:
                if "Reachability Percentage" in stripped_line:
                    text = "Reachable/(Total-User Excluded)"
                    legend.append(f"<strong>Reachability Percentage</strong>: {text}")
                else:
                    parts = stripped_line.split(" ", 1)
                    if len(parts) == 2:
                        legend.append(f"<strong>{parts[0]}</strong>: {parts[1]}")

        if "Assumptions" in stripped_line:
            current_section = "Assumptions"
            assumptions = []
            match = re.search(r"Assumptions \((\d+)\)", stripped_line)
            if match:
                assumptions_count = match.group(1)
                assumptions.append(f"<h2>Assumptions ({assumptions_count})</h2><ul>")
            continue

        if current_section == "Assumptions":
            if stripped_line == "":
                current_section = None
            else:
                assumptions.append(stripped_line)

        if re.match(r"Reachability Summary for Design:", stripped_line):
            table_title = stripped_line
            current_section = "Design"
            index_items.append((current_section, table_title))
            continue

        if re.match(r"Reachability Summary for Instance:", stripped_line):
            table_title = stripped_line
            current_section = "Instance"
            index_items.append((current_section, table_title))
            continue

        if "Cover Type" in stripped_line and not cover_table:
            cover_table = True
            cover_type_table = [["Cover Type","Total","Unreachable","Inconclusive","Reachable"]]
            continue

        if cover_table:
            if stripped_line == "" or "Total" in stripped_line:
                if cover_type_table:
                    tables.append((table_title, cover_type_table))
                cover_table = False
                continue

            row = re.split(r"\s{3,}", stripped_line)
            if len(row) >= 5:
                row[4] = re.sub(r"\s*\)$", r" )", row[4])
                row = row[:5]
            if row:
                cover_type_table.append(row)

    html_content.append("""<!DOCTYPE html>
    <html lang='en'>
    <head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Reachability Report</title>
    <link href='https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap'
          rel='stylesheet'>
    <style>
    body {
        font-family: 'Poppins',
        sans-serif;
        margin: 0;
        padding: 15px;
        background-color: #f4f4f9;
        color: #333;
        line-height: 1.4;
        font-size: 14px;
    }
    h1, h2, h3 {
        text-align: center;
        margin-bottom: 8px;
        font-weight: 600;
        font-size: 1.5em;
    }
    .container {
        display: flex;
        height: 100h;
        overflow: hidden;
    }
    .index {
        flex: 1;
        max-width: 25%;
        padding: 15px;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow-y: scroll;
        height: 100%;
    }
    .content { 
        flex: 4;
        padding: 15px;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow-y: scroll;
        height: 100%;
    }
    table {
        width: 80%;
        border-collapse: collapse;
        margin: 20px auto;
        background-color: #fff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-size: 14px;
    }
    table th, table td {
        padding: 10px 12px;
        text-align: center;
    }
    table th {
        background-color: #1976D2;
        color: white;
        font-weight: 600;
    }
    table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    table tr:hover {
        background-color: #f1f1f1;
    }
    .legend, .assumptions, .assertions, .index {
        margin: 20px auto;
        padding: 15px;
        width: 75%;
        text-align: left;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        font-size: 14px; 
    }
    .legend ul, .assumptions ul, .assertions ul, .index ul {
        list-style-type: none; padding: 0; margin: 0;
    }
    .legend ul li, .assumptions ul li, .assertions ul li, .index ul li {
        margin: 8px 0; font-size: 1em;
    }
    .legend h2, .assumptions h2, .assertions h2, .index h2  {
        font-weight: 600; font-size: 1.2em;
    }
    .index ul li { margin: 8px 0; font-size: 1em; }
    .index ul li a { color: #0000EE; text-decoration: none; }
    .index ul li a:visited { color: #0000EE; }
    .index ul li a:hover { color: #0000EE; }
    .index ul li a:active { color: #0000EE; }
    .index ul li.index_instance {
        padding-left: 20px;
        font-style: italic; 
    }
    .toggle-btn {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        background: none;
        border: none;
        padding: 10px 0;
        cursor: pointer;
        text-align: center;
        width: 100%;
        margin-bottom: 10px;
    }
    .tables-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        width: 80%;
        margin: 0 auto;
        background-color: transparent;
    }
    table {
        width: 80%;
        border-collapse: collapse;
        margin: 20px auto;
        background-color: #fff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-size: 14px;
    }
    .content .legend, .content .assumptions, .content .tables-container { margin-bottom: 20px; }
    </style>
    </head>
    <body>
    <h1>Reachability Report</h1>""")

    if report_generated:
        match = re.match(r"(Report Generated :)(.*)", report_generated)
        if match:
            bold_text = match.group(1).strip()
            normal_text = match.group(2).strip()
            html_content.append(
                f"<p style='text-align: center;'><strong>{bold_text}</strong> {normal_text}</p>"
            )
    html_content.append("<div class='container'>")
    if index_items:
        html_content.append("<div class='index'>")
        html_content.append("<h2>Index</h2>")
        html_content.append("<ul>")
        for idx, (section_type, item) in enumerate(index_items):
            link_id = f"table_title_{idx}"

            if section_type == "Design":
                item_text = item.split(":")[-1].strip()
                html_content.append(
                    f"<li><a href='#{link_id}'>{section_type}: {item_text}</a></li>"
                    )
            if section_type == "Instance":
                item_text = item.split(":")[-1].strip()
                html_content.append(
                    f"<li class='index_instance'><a href='#{link_id}'>"
                    f"{section_type}: {item_text}</a></li>"
                )
        html_content.append("</ul>")
        html_content.append("</div>")

    html_content.append("<div class='content'>")

    if assumptions:
        html_content.append("<div class='assumptions'><h2></h2><ul>")
        for item in assumptions:
            html_content.append(f"<li>{item}</li>")
        html_content.append("</ul></div>")

    if tables:
        html_content.append("<div class='tables-container'>")

        for idx, (table_title, table) in enumerate(tables):
            title_id = f"table_title_{idx}"

            html_content.append(
                f"<button class='toggle-btn' id='{title_id}' "
                f"onclick='toggleTable(\"table_{idx}\")'>{table_title}</button>"
            )

            html_content.append(
                f"<div id='table_{idx}' class='table-content' "
                f"style='display: block; margin-bottom: 20px;'>"
            )

            html_content.append("<table><thead><tr>")
            for header in table[0]:
                html_content.append(f"<th>{header}</th>")
            html_content.append("</tr></thead><tbody>")

            for i, row in enumerate(table[1:]):
                row_color = "#f9f9f9" if i % 2 == 0 else "#e0e0e0"
                html_content.append(f"<tr style='background-color: {row_color};'>")
                for idx, cell in enumerate(row):
                    if idx == 4:
                        match = re.search(r"(\d+(\.\d+)?)%", cell)
                        if match:
                            percentage = float(match.group(1))
                            if 80 <= percentage < 90:
                                html_content.append(
                                    f"<td style=background-color:#A5D6A7;color:black>{cell}</td>"
                                )
                            elif 90 <= percentage <= 100:
                                html_content.append(
                                    f"<td style=background-color:#66bb6a;color:black>{cell}</td>"
                                )
                            elif 60 <= percentage < 80:
                                html_content.append(
                                    f"<td style=background-color:#FFF59D;color:black>{cell}</td>"
                                )
                            elif 30 <= percentage < 60:
                                html_content.append(
                                    f"<td style=background-color:#FFEB3B;color:black>{cell}</td>"
                                )
                            else:
                                html_content.append(
                                    f"<td style=background-color:#FF7043;color:black>{cell}</td>"
                                )
                        else:
                            html_content.append(f"<td>{cell}</td>")
                    else:
                        html_content.append(f"<td>{cell}</td>")
                html_content.append("</tr>")
            html_content.append("</tbody></table>")
            html_content.append("</div>")

        html_content.append("</div>")

    html_content.append("<script>")
    html_content.append("function toggleTable(tableId) {")
    html_content.append("  var table = document.getElementById(tableId);")
    html_content.append("  if (table.style.display === 'none') {")
    html_content.append("    table.style.display = 'block';")
    html_content.append("  } else {")
    html_content.append("    table.style.display = 'none';")
    html_content.append("  }")
    html_content.append("}")
    html_content.append("</script>")
    html_content.append("</div>")
    html_content.append("</div>")
    html_content.append("</body>")
    html_content.append("</html>")

    with open(output_file, "w", encoding="utf-8") as output:
        output.write("\n".join(html_content))

def parse_formal_observability_report_to_html(input_file, output_file="report.html"):
    """Parses a formal observability report text file and converts it to an
    HTML file with styling and interactivity."""
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    html_content = []
    assumptions = []
    assertions = []
    index_items = []
    tables = []
    current_section = None
    legend = []
    cover_table = False
    cover_type_table = []
    table_title = ""
    report_generated = ""

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("Report Generated :"):
            report_generated = stripped_line
            continue

        if re.search(r"-{2,}", stripped_line):
            continue

        if "Legend" in stripped_line:
            current_section = "Legend"
            legend = []
            continue

        if current_section == "Legend":
            if stripped_line == "":
                current_section = None
            else:
                if "Observability Percentage" in stripped_line:
                    text = "Observable/(Total-User Excluded)"
                    legend.append(f"<strong>Observability Percentage</strong>: {text}")
                else:
                    parts = stripped_line.split(" ", 1)
                    if len(parts) == 2:
                        legend.append(f"<strong>{parts[0]}</strong>: {parts[1]}")

        if "Assumptions" in stripped_line:
            current_section = "Assumptions"
            assumptions = []
            match = re.search(r"Assumptions \((\d+)\)", stripped_line)
            if match:
                assumptions_count = match.group(1)
                assumptions.append(f"<h2>Assumptions ({assumptions_count})</h2><ul>")
            continue

        if current_section == "Assumptions":
            if stripped_line == "":
                current_section = None
            else:
                assumptions.append(stripped_line)

        if "Formal Coverage Report Generated for Proven Targets" in stripped_line:
            current_section = "Assertions"
            assertions = []
            match = re.search(
                r"Formal Coverage Report Generated for Proven Targets \((\d+)\)",
                stripped_line
            )
            if match:
                assertions_count = match.group(1)
                assertions.append(
                    f"<h2>Formal Coverage Report Generated for Proven Targets "
                    f"({assertions_count})</h2><ul>"
                )

        if current_section == "Assertions":
            if stripped_line == "":
                current_section = None
            else:
                assertions.append(stripped_line)

        if re.match(r"Observability Summary for Design:", stripped_line):
            table_title = stripped_line
            current_section = "Design"
            index_items.append((current_section, table_title))
            continue

        if re.match(r"Observability Summary for Instance:", stripped_line):
            table_title = stripped_line
            current_section = "Instance"
            index_items.append((current_section, table_title))
            continue

        if "Cover Type" in stripped_line and not cover_table:
            cover_table = True
            cover_type_table = [["Cover Type", "Total", "Unobservable", "Observable (P)"]]
            continue

        if cover_table:
            if stripped_line == "" or "Total" in stripped_line:
                if cover_type_table:
                    tables.append((table_title, cover_type_table))
                cover_table = False
                continue

            row = re.split(r"\s{3,}", stripped_line)
            if len(row) >= 4:
                row[3] = re.sub(r"\s*\)$", r" )", row[3])
                row = row[:4]
            if row:
                cover_type_table.append(row)

    html_content.append("""<!DOCTYPE html>
    <html lang='en'>
    <head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Observability Report</title>
    <link href='https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap'
          rel='stylesheet'>
    <style>
    body {
        font-family: 'Poppins',
        sans-serif;
        margin: 0;
        padding: 15px;
        background-color: #f4f4f9;
        color: #333;
        line-height: 1.4;
        font-size: 14px;
    }
    h1, h2, h3 {
        text-align: center;
        margin-bottom: 8px;
        font-weight: 600;
        font-size: 1.5em;
    }
    .container {
        display: flex;
        height: 100h;
        overflow: hidden;
    }
    .index {
        flex: 1;
        max-width: 25%;
        padding: 15px;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow-y: scroll;
        height: 100%;
    }
    .content {
        flex: 4;
        padding: 15px;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow-y: scroll;
        height: 100%;
    }
    table {
        width: 80%;
        border-collapse: collapse;
        margin: 20px auto;
        background-color: #fff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-size: 14px;
    }
    table th, table td {
        padding: 10px 12px;
        text-align: center;
    }
    table th {
        background-color: #1976D2;
        color: white;
        font-weight: 600;
    }
    table tr:nth-child(even) { background-color: #f9f9f9; }
    table tr:hover { background-color: #f1f1f1; }
    .legend, .assumptions, .assertions, .index {
        margin: 20px auto;
        padding: 15px;
        width: 75%;
        text-align: left;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        font-size: 14px;
    }
    .legend ul, .assumptions ul, .assertions ul, .index ul { 
        list-style-type: none;
        padding: 0;
        margin: 0;
    }
    .legend ul li, .assumptions ul li, .assertions ul li, .index ul li {
        margin: 8px 0;
        font-size: 1em;
    }
    .legend h2, .assumptions h2, .assertions h2, .index h2  {
        font-weight: 600;
        font-size: 1.2em;
    }
    .index ul li { 
        margin: 8px 0;
        font-size: 1em;
    }
    .index ul li a {
        color: #0000EE;
        text-decoration: none;
    }
    .index ul li a:visited { color: #0000EE; }
    .index ul li a:hover { color: #0000EE; }
    .index ul li a:active { color: #0000EE; }
    .index ul li.index_instance {
        padding-left: 20px;
        font-style: italic;
    }
    .toggle-btn {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        background: none;
        border: none;
        padding: 10px 0;
        cursor: pointer;
        text-align: center;
        width: 100%;
        margin-bottom: 10px;
    }
    .tables-container {
        display: flex;
        flex-direction: column;
        gap: 20px; width: 80%;
        margin: 0 auto;
        background-color: transparent;
    }
    table {
        width: 80%;
        border-collapse: collapse;
        margin: 20px auto;
        background-color: #fff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-size: 14px;
    }
    .content .legend, .content .assumptions, .content .tables-container { margin-bottom: 20px; }
    </style>
    </head>
    <body>
    <h1>Observability Report</h1>""")

    if report_generated:
        match = re.match(r"(Report Generated :)(.*)", report_generated)
        if match:
            bold_text = match.group(1).strip()
            normal_text = match.group(2).strip()
            html_content.append(
                f"<p style='text-align: center;'><strong>{bold_text}</strong> {normal_text}</p>"
            )

    html_content.append("<div class='container'>")
    if index_items:
        html_content.append("<div class='index'>")
        html_content.append("<h2>Index</h2>")
        html_content.append("<ul>")
        for idx, (section_type, item) in enumerate(index_items):
            link_id = f"table_title_{idx}"

            if section_type == "Design":
                item_text = item.split(":")[-1].strip()
                html_content.append(
                    f"<li><a href='#{link_id}'>{section_type}: {item_text}</a></li>"
                    )
            if section_type == "Instance":
                item_text = item.split(":")[-1].strip()
                html_content.append(
                    f"<li class='index_instance'><a href='#{link_id}'>"
                    f"{section_type}: {item_text}</a></li>"
                )
        html_content.append("</ul>")
        html_content.append("</div>")

    html_content.append("<div class='content'>")

    if assumptions:
        html_content.append("<div class='assumptions'><h2></h2><ul>")
        for item in assumptions:
            html_content.append(f"<li>{item}</li>")
        html_content.append("</ul></div>")

    if assertions:
        html_content.append("<div class='assertions'><h2></h2><ul>")
        for item in assertions:
            html_content.append(f"<li>{item}</li>")
        html_content.append("</ul></div>")

    if tables:
        html_content.append("<div class='tables-container'>")

        for idx, (table_title, table) in enumerate(tables):
            title_id = f"table_title_{idx}"

            html_content.append(
                f"<button class='toggle-btn' id='{title_id}' "
                f"onclick='toggleTable(\"table_{idx}\")'>{table_title}</button>"
            )

            html_content.append(
                f"<div id='table_{idx}' class='table-content' "
                f"style='display: block; margin-bottom: 20px;'>"
            )

            html_content.append("<table><thead><tr>")
            for header in table[0]:
                html_content.append(f"<th>{header}</th>")
            html_content.append("</tr></thead><tbody>")

            for i, row in enumerate(table[1:]):
                row_color = "#f9f9f9" if i % 2 == 0 else "#e0e0e0"
                html_content.append(f"<tr style='background-color: {row_color};'>")
                for idx, cell in enumerate(row):
                    if idx == 3:
                        match = re.search(r"(\d+(\.\d+)?)%", cell)
                        if match:
                            percentage = float(match.group(1))
                            if 80 <= percentage < 90:
                                html_content.append(
                                    f"<td style=background-color:#A5D6A7;color:black>{cell}</td>"
                                )
                            elif 90 <= percentage <= 100:
                                html_content.append(
                                    f"<td style=background-color:#66bb6a;color:black>{cell}</td>"
                                )
                            elif 60 <= percentage < 80:
                                html_content.append(
                                    f"<td style=background-color:#FFF59D;color:black>{cell}</td>"
                                )
                            elif 30 <= percentage < 60:
                                html_content.append(
                                    f"<td style=background-color:#FFEB3B;color:black>{cell}</td>"
                                )
                            else:
                                html_content.append(
                                    f"<td style=background-color:#FF7043;color:black>{cell}</td>"
                                )
                        else:
                            html_content.append(f"<td>{cell}</td>")
                    else:
                        html_content.append(f"<td>{cell}</td>")
                html_content.append("</tr>")
            html_content.append("</tbody></table>")
            html_content.append("</div>")

        html_content.append("</div>")

    html_content.append("<script>")
    html_content.append("function toggleTable(tableId) {")
    html_content.append("  var table = document.getElementById(tableId);")
    html_content.append("  if (table.style.display === 'none') {")
    html_content.append("    table.style.display = 'block';")
    html_content.append("  } else {")
    html_content.append("    table.style.display = 'none';")
    html_content.append("  }")
    html_content.append("}")
    html_content.append("</script>")
    html_content.append("</div>")
    html_content.append("</div>")
    html_content.append("</body></html>")

    with open(output_file, "w", encoding="utf-8") as output:
        output.write("\n".join(html_content))

def parse_reachability_report_to_html(input_file, output_file="report.html"):
    """Parses a reachability report text file and converts it to an
    HTML file with styling and interactivity."""
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    html_content = []
    tables = []
    cover_table = False
    cover_type_table = []
    table_title = ""
    report_generated = ""

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("Report Generated               :"):
            report_generated = stripped_line
            continue

        if re.search(r"-{2,}", stripped_line):
            continue

        if re.match(r"Summary", stripped_line):
            table_title = stripped_line
            continue

        if "Coverage Type" in stripped_line and not cover_table:
            cover_table = True
            cover_type_table = [["Coverage Type","Active","Witness","Inconclusive","Unreachable"]]
            continue

        if cover_table:
            if stripped_line == "" or "Total" in stripped_line:
                if cover_type_table:
                    tables.append((table_title, cover_type_table))
                cover_table = False
                continue

            row = re.split(r"\s{3,}", stripped_line)
            if len(row) >= 5:
                row[4] = re.sub(r"\s*\)$", r" )", row[4])
                row = row[:5]
            if row:
                cover_type_table.append(row)

    html_content.append("""<!DOCTYPE html>
    <html lang='en'>
    <head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>CoverCheck Reachability Report</title>
    <link href='https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap'
          rel='stylesheet'>
    <style>
    body {
        font-family: 'Poppins', sans-serif;
        margin: 0;
        padding: 15px;
        background-color: #f4f4f9;
        color: #333;
        line-height: 1.4;
        font-size: 14px;
    }
    h1, h2, h3 {
        text-align: center;
        margin-bottom: 8px;
        font-weight: 600;
        font-size: 1.5em;
    }
    table {
        width: 80%;
        border-collapse: collapse;
        margin: 20px auto;
        background-color: #fff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-size: 14px;
    }
    table th, table td {
        padding: 10px 12px;
        text-align: center;
    }
    table th {
        background-color: #1976D2;
        color: white;
        font-weight: 600;
    }
    table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    table tr:hover {
        background-color: #f1f1f1;
    }
    .legend, .assumptions {
        margin: 20px auto;
        padding: 15px;
        width: 75%;
        text-align: left;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        font-size: 14px;
    }
    .legend ul, .assumptions ul {
        list-style-type: none;
        padding: 0;
        margin: 0;
    }
    .legend ul li, .assumptions ul li {
        margin: 8px 0;
        font-size: 1em;
    }
    .legend h2, .assumptions h2 {
        font-weight: 600;
        font-size: 1.2em;
    }
    </style>
    </head>
    <body>
    <h1>CoverCheck Reachability Report</h1>""")

    if report_generated:
        match = re.match(r"(Report Generated               :)(.*)", report_generated)
        if match:
            bold_text = match.group(1).strip()
            normal_text = match.group(2).strip()
            html_content.append(
                f"<p style='text-align: center;'><strong>{bold_text}</strong> {normal_text}</p>"
            )

    for table_title, table in tables:
        for line in table_title.split("\n"):
            html_content.append(f"<h2>{line}</h2>")
        html_content.append("<table><thead><tr>")
        for header in table[0]:
            html_content.append(f"<th>{header}</th>")
        html_content.append("</tr></thead><tbody>")

        for i, row in enumerate(table[1:]):
            row_color = "#f9f9f9" if i % 2 == 0 else "#e0e0e0"
            html_content.append(f"<tr style='background-color: {row_color};'>")
            for idx, cell in enumerate(row):
                if idx == 4:
                    match = re.search(r"(\d+(\.\d+)?)%", cell)
                    if match:
                        percentage = float(match.group(1))
                        if 80 <= percentage < 90:
                            html_content.append(
                                f"<td style=background-color:#A5D6A7;color:black>{cell}</td>"
                            )
                        elif 90 <= percentage <= 100:
                            html_content.append(
                                f"<td style=background-color:#66bb6a;color:black>{cell}</td>"
                            )
                        elif 60 <= percentage < 80:
                            html_content.append(
                                f"<td style=background-color:#FFF59D;color:black>{cell}</td>"
                            )
                        elif 30 <= percentage < 60:
                            html_content.append(
                                f"<td style=background-color:#FFEB3B;color:black>{cell}</td>"
                            )
                        else:
                            html_content.append(
                                f"<td style=background-color:#FF7043;color:black>{cell}</td>"
                            )
                    else:
                        html_content.append(f"<td>{cell}</td>")
                else:
                    html_content.append(f"<td>{cell}</td>")
            html_content.append("</tr>")
        html_content.append("</tbody></table>")

    html_content.append("</body>")
    html_content.append("</html>")

    with open(output_file, "w", encoding="utf-8") as output:
        output.write("\n".join(html_content))

def parse_formal_signoff_report_to_html(input_file, output_file="report.html"):
    """Parses a formal signoff report text file and converts it to an
    HTML file with styling and interactivity."""
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    html_content = []
    assumptions = []
    index_items = []
    assertions = []
    tables = []
    current_section = None
    legend = []
    cover_table = False
    cover_type_table = []
    table_title = ""
    report_generated = ""

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("Report Generated :"):
            report_generated = stripped_line
            continue

        if re.search(r"-{2,}", stripped_line):
            continue

        if "Legend" in stripped_line:
            current_section = "Legend"
            legend = []
            continue

        if current_section == "Legend":
            if stripped_line == "":
                current_section = None
            else:
                if "Covered Percentage" in stripped_line:
                    text = "Covered / (Total - Excluded)"
                    legend.append(f"<strong>Covered Percentage</strong>: {text}")
                else:
                    parts = stripped_line.split(" ", 1)
                    if len(parts) == 2:
                        legend.append(f"<strong>{parts[0]}</strong>: {parts[1]}")

        if "Assumptions" in stripped_line:
            current_section = "Assumptions"
            assumptions = []
            match = re.search(r"Assumptions \((\d+)\)", stripped_line)
            if match:
                assumptions_count = match.group(1)
                assumptions.append(f"<h2>Assumptions ({assumptions_count})</h2><ul>")
            continue

        if current_section == "Assumptions":
            if stripped_line == "":
                current_section = None
            else:
                assumptions.append(stripped_line)

        if re.match(r"Formal Coverage Summary for Design:", stripped_line):
            table_title = stripped_line
            current_section = "Design"
            index_items.append((current_section, table_title))
            continue

        if re.match(r"Formal Coverage Summary for Instance:", stripped_line):
            table_title = stripped_line
            current_section = "Instance"
            index_items.append((current_section, table_title))
            continue

        if "Formal Coverage Report Generated for Proven Targets" in stripped_line:
            current_section = "Assertions"
            assertions = []
            match = re.search(
                r"Formal Coverage Report Generated for Proven Targets \((\d+)\)",
                stripped_line
            )
            if match:
                assertions_count = match.group(1)
                assertions.append(
                    f"<h2>Formal Coverage Report Generated for Proven Targets "
                    f"({assertions_count})</h2><ul>"
                )

        if current_section == "Assertions":
            if stripped_line == "":
                current_section = None
            else:
                assertions.append(stripped_line)

        if "Coverage Type" in stripped_line and not cover_table:
            cover_table = True
            cover_type_table = []
            continue

        if cover_table:
            if stripped_line == "" or "Total" in stripped_line:
                if cover_type_table:
                    tables.append((table_title, cover_type_table))
                cover_table = False
                continue

            row = re.split(r"\s{3,}", stripped_line)
            if len(row) >= 4:
                if not cover_type_table:
                    if len(row) == 5:
                        cover_type_table.append([
                            "Coverage Type",
                            "Total",
                            "Uncovered",
                            "Excluded",
                            "Covered (P)"
                        ])
                    elif len(row) == 4:
                        cover_type_table.append([
                            "Coverage Type",
                            "Total",
                            "Uncovered",
                            "Covered (P)"
                        ])
                cover_type_table.append(row)

    html_content.append("""<!DOCTYPE html>
    <html lang='en'>
    <head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Signoff Report</title>
    <link href='https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap'
        rel='stylesheet'>
    <style>
    body {
        font-family: 'Poppins', sans-serif;
        margin: 0;
        padding: 15px;
        background-color: #f4f4f9;
        color: #333;
        line-height: 1.4;
        font-size: 14px;
    }
    h1, h2, h3 {
        text-align: center;
        margin-bottom: 8px;
        font-weight: 600;
        font-size: 1.5em;
    }
    .container {
        display: flex;
        height: 100h;
        overflow: hidden;
    }
    .index {
        flex: 1;
        max-width: 25%;
        padding: 15px;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow-y: scroll;
        height: 100%;
    }
    .content {
        flex: 4;
        padding: 15px;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow-y: scroll;
        height: 100%;
    }
    table {
        width: 80%;
        border-collapse: collapse;
        margin: 20px auto;
        background-color: #fff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-size: 14px;
    }
    table th, table td {
        padding: 10px 12px;
        text-align: center;
    }
    table th {
        background-color: #1976D2;
        color: white;
        font-weight: 600;
    }
    table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    table tr:hover {
        background-color: #f1f1f1;
    }
    .legend, .assumptions, .assertions, .index {
        margin: 20px auto;
        padding: 15px;
        width: 75%;
        text-align: left;
        background-color: #fff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        font-size: 14px;
    }
    .legend ul, .assumptions ul, .assertions ul, .index ul {
        list-style-type: none;
        padding: 0;
        margin: 0;
    }
    .legend ul li, .assumptions ul li, .assertions ul li, .index ul li {
        margin: 8px 0;
        font-size: 1em;
    }
    .legend h2, .assumptions h2, .assertions h2, .index h2 {
        font-weight: 600;
        font-size: 1.2em;
    }
    .index ul li { margin: 8px 0; font-size: 1em; }
    .index ul li a { color: #0000EE; text-decoration: none; }
    .index ul li a:visited { color: #0000EE; }
    .index ul li a:hover { color: #0000EE; }
    .index ul li a:active { color: #0000EE; }
    .index ul li.index_instance {
        padding-left: 20px;
        font-style: italic;
    }
    .toggle-btn {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        background: none;
        border: none;
        padding: 10px 0;
        cursor: pointer;
        text-align: center;
        width: 100%;
        margin-bottom: 10px;
    }
    .tables-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        width: 80%;
        margin: 0 auto;
        background-color: transparent;
    }
    .content .legend, .content .assumptions, .content .tables-container {
        margin-bottom: 20px;
    }
    </style>
    </head>
    <body>
    <h1>Signoff Report</h1>""")

    if report_generated:
        match = re.match(r"(Report Generated :)(.*)", report_generated)
        if match:
            bold_text = match.group(1).strip()
            normal_text = match.group(2).strip()
            html_content.append(
                f"<p style='text-align: center;'><strong>{bold_text}</strong> {normal_text}</p>"
            )

    html_content.append("<div class='container'>")
    if index_items:
        html_content.append("<div class='index'>")
        html_content.append("<h2>Index</h2>")
        html_content.append("<ul>")
        for idx, (section_type, item) in enumerate(index_items):
            link_id = f"table_title_{idx}"

            if section_type == "Design":
                item_text = item.split(":")[-1].strip()
                html_content.append(
                    f"<li><a href='#{link_id}'>{section_type}: {item_text}</a></li>"
                    )
            if section_type == "Instance":
                item_text = item.split(":")[-1].strip()
                html_content.append(
                    f"<li class='index_instance'><a href='#{link_id}'>"
                    f"{section_type}: {item_text}</a></li>"
                )
        html_content.append("</ul>")
        html_content.append("</div>")

    html_content.append("<div class='content'>")


    if assumptions:
        html_content.append("<div class='assumptions'><h2></h2><ul>")
        for item in assumptions:
            html_content.append(f"<li>{item}</li>")
        html_content.append("</ul></div>")

    if assertions:
        html_content.append("<div class='assertions'><h2></h2><ul>")
        for item in assertions:
            html_content.append(f"<li>{item}</li>")
        html_content.append("</ul></div>")

    if tables:
        html_content.append("<div class='tables-container'>")

        for idx, (table_title, table) in enumerate(tables):
            title_id = f"table_title_{idx}"

            html_content.append(
                f"<button class='toggle-btn' id='{title_id}' "
                f"onclick='toggleTable(\"table_{idx}\")'>{table_title}</button>"
            )

            html_content.append(
                f"<div id='table_{idx}' class='table-content' "
                f"style='display: block; margin-bottom: 20px;'>"
            )

            html_content.append("<table><thead><tr>")
            for header in table[0]:
                html_content.append(f"<th>{header}</th>")
            html_content.append("</tr></thead><tbody>")

            for i, row in enumerate(table[1:]):
                row_color = "#f9f9f9" if i % 2 == 0 else "#e0e0e0"
                html_content.append(f"<tr style='background-color: {row_color};'>")
                for idx, cell in enumerate(row):
                    if idx in (3, 4):
                        match = re.search(r"(\d+(\.\d+)?)%", cell)
                        if match:
                            percentage = float(match.group(1))
                            if 80 <= percentage < 90:
                                html_content.append(
                                    f"<td style=background-color:#A5D6A7;color:black>{cell}</td>"
                                )
                            elif 90 <= percentage <= 100:
                                html_content.append(
                                    f"<td style=background-color:#66bb6a;color:black>{cell}</td>"
                                )
                            elif 60 <= percentage < 80:
                                html_content.append(
                                    f"<td style=background-color:#FFF59D;color:black>{cell}</td>"
                                )
                            elif 30 <= percentage < 60:
                                html_content.append(
                                    f"<td style=background-color:#FFEB3B;color:black>{cell}</td>"
                                )
                            else:
                                html_content.append(
                                    f"<td style=background-color:#FF7043;color:black>{cell}</td>"
                                )
                        else:
                            html_content.append(f"<td>{cell}</td>")
                    else:
                        html_content.append(f"<td>{cell}</td>")
                html_content.append("</tr>")
            html_content.append("</tbody></table>")
            html_content.append("</div>")

        html_content.append("</div>")

    html_content.append("<script>")
    html_content.append("function toggleTable(tableId) {")
    html_content.append("  var table = document.getElementById(tableId);")
    html_content.append("  if (table.style.display === 'none') {")
    html_content.append("    table.style.display = 'block';")
    html_content.append("  } else {")
    html_content.append("    table.style.display = 'none';")
    html_content.append("  }")
    html_content.append("}")
    html_content.append("</script>")

    html_content.append("</div>")
    html_content.append("</div>")

    html_content.append("</body>")
    html_content.append("</html>")

    with open(output_file, "w", encoding="utf-8") as output:
        output.write("\n".join(html_content))
