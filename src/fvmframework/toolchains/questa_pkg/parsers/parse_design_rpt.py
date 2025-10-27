"""Parsers for friendliness score"""
import re
import math

def get_design_summary(filename):
    """Extracts the design summary section from a design report file."""
    summary = []
    found = False
    with open(filename, "r", encoding="utf-8") as f:
        # Get all lines between "Design Summary" and
        # "User-specified Constant Bits"
        for line in f:
            if "Design Summary" in line:
                found = True
            if found:
                summary.append(line)
            if "User-specified Constant Bits" in line:
                break
    return summary

def parse_design_summary(summary):
    """Parses the design summary section and returns a list of lists with
    category, statistic, count"""
    data = []
    for line in summary:
        match = re.match(r'^( {0,2})(.*\S)\s+(\d+)$', line)
        if match:
            # Capture leading spaces to determine category level
            leading_spaces = match.group(1)
            category = 'Subcategory' if len(leading_spaces) == 2 else 'Top-level'
            statistic = match.group(2).strip()
            count = int(match.group(3))
            data.append([category, statistic, count])
        elif "Storage Structures" in line:
            # This is a special case because it depends on what is below
            category = "Top-level"
            statistic = "Storage Structures"
            count = 'see below'
            data.append([category, statistic, count])
    return data

def update_storage_structures(data):
    """Updates the 'Storage Structures' row with the total number of
    storage structures found in the design summary."""
    # Since the report doesn't include the total number of storage structures,
    # let's add it
    total = 0
    # Get the total
    search_terms = ["Counters", "FSMs", "RAMs"]
    for row in data:
        for term in search_terms:
            if term in row[1] :
                total += row[2]
    # Update the relevant field
    for row in data:
        if "Storage Structures" in row[1]:
            row[2] = total
    return data

def data_from_design_summary(filename):
    """Extracts and parses the design summary from a design report file."""
    summary = get_design_summary(filename)
    data = parse_design_summary(summary)
    data = update_storage_structures(data)
    return data

def difficulty_score(data):
    """Computes an overall formal difficulty score according to a weighted
    operation of the number of elements in the design. Currently the operation
    is just a sum but it could be an exponential function in the future"""
    SCORE_WEIGHTS = {
            'Clocks'             : 500,
            'Resets'             : 250,
            'Control Point Bits' : 4,
            'State Bits'         : 5,
            'Counters'           : 40,
            'FSMs'               : 80,
            'RAMs'               : 100
            }
    difficulty = 0
    for row in data:
        for term, weight in SCORE_WEIGHTS.items():
            if term in row[1]:
                #print(f'found:{row=}')
                if row[1] in ['Clocks', 'Resets']:
                    number = row[2] - 1
                else:
                    number = row[2]

                difficulty += number*weight
    return difficulty

def difficulty_to_friendliness(difficulty):
    """Converts difficulty score to a friendliness percentage"""
    DECAY = 0.00008 # Makes the exponential decay slower
    percentage = 100 / (math.log(DECAY*difficulty+1) + 1)
    return percentage

def friendliness_score(data):
    """Computes the friendliness score"""
    return difficulty_to_friendliness(difficulty_score(data))
