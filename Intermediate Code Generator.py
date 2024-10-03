import re

def get_temp_var(temp_var_count):
    return f"t{temp_var_count}"

def handle_expression(expression, temp_var_count):
    """
   In this function we Handle expressions with multiple operands by breaking them down into smaller steps.
    """
    tokens = re.split(r'(\+|\-|\*|\/)', expression.replace(' ', ''))
    tac = []
    
    while len(tokens) > 1:
        left_operand = tokens.pop(0)
        operator = tokens.pop(0)
        right_operand = tokens.pop(0)
        temp_var = get_temp_var(temp_var_count)
        tac.append(f"{temp_var} = {left_operand} {operator} {right_operand}")
        tokens.insert(0, temp_var)
        temp_var_count += 1
    
    return tokens[0], temp_var_count, tac

def handle_declaration(line, temp_var_count):
    tac = []
    var_name = line.split()[1].replace(";", "")
    tac.append(f"Declare {var_name.strip()}")
    return tac, temp_var_count

def handle_if_else(statement, temp_var_count, label_count):
    tac = []
    match = re.search(r'if\s*\((.*?)\)', statement)
    if match:
        condition = match.group(1)
        temp_var = get_temp_var(temp_var_count)
        tac.append(f"{temp_var} = {condition.strip()}")
        tac.append(f"IF {temp_var} == 0 GOTO L{label_count + 1}")  
        temp_var_count += 1
        tac.append(f"GOTO L{label_count + 2}")  
        tac.append(f"L{label_count + 1}:")  
    return tac, temp_var_count, label_count + 2  

def handle_loop(statement, loop_type, temp_var_count, label_count):
    tac = []
    if loop_type == "for":
        match = re.search(r'for\s*\((.*?);(.*?);(.*?)\)', statement)
        if match:
            init, condition, increment = match.groups()
            tac.append(f"{init.strip()}")
            tac.append(f"L{label_count}:")
            temp_var = get_temp_var(temp_var_count)
            tac.append(f"{temp_var} = {condition.strip()}")
            tac.append(f"IF {temp_var} == 0 GOTO L{label_count + 1}")
            temp_var_count += 1
            label_count += 2
            tac.append(f"{increment.strip()}")
            tac.append(f"GOTO L{label_count - 2}")
    elif loop_type == "while":
        match = re.search(r'while\s*\((.*?)\)', statement)
        if match:
            condition = match.group(1)
            tac.append(f"L{label_count}:")
            temp_var = get_temp_var(temp_var_count)
            tac.append(f"{temp_var} = {condition.strip()}")
            tac.append(f"IF {temp_var} == 0 GOTO L{label_count + 1}")
            temp_var_count += 1
            label_count += 1
    return tac, temp_var_count, label_count

def handle_switch(statement, temp_var_count, label_count):
    tac = []
    match = re.search(r'switch\s*\((.*?)\)', statement)
    if match:
        switch_var = match.group(1).strip()
        tac.append(f"SWITCH {switch_var}")
        label_count += 1  
    return tac, temp_var_count, label_count

def handle_case(statement, temp_var_count, label_count):
    tac = []
    match = re.search(r'case\s+(.*?):', statement)
    if match:
        case_value = match.group(1).strip()
        tac.append(f"L{label_count}:")  
        tac.append(f"IF {case_value} == {case_value} GOTO L{label_count}")
    return tac, temp_var_count, label_count + 1

def handle_default(label_count):
    tac = []
    tac.append(f"L{label_count}:")
    return tac

def handle_function_call(line, temp_var_count):
    tac = []
    function_name = re.match(r'(\w+)\s*\((.*?)\)', line)
    if function_name:
        function_name = function_name.group(1)
        tac.append(f"CALL {function_name}")
    return tac, temp_var_count

def generate_TAC_from_C_code(c_code):
    tac = []
    temp_var_count = 1
    label_count = 1
    lines = c_code.splitlines()

    for line in lines:
        line = line.strip()
        
        if line.startswith("int") or line.startswith("float") or line.startswith("double") or line.startswith("char"):
            declaration_tac, temp_var_count = handle_declaration(line, temp_var_count)
            tac.extend(declaration_tac)
        
        elif '=' in line and not any(op in line for op in ['==', '!=', '<', '>', '<=', '>=']):
            parts = line.split('=', 1)
            var_name = parts[0].strip()
            expression = parts[1].strip(';')
            result, temp_var_count, expression_tac = handle_expression(expression, temp_var_count)
            tac.extend(expression_tac)
            tac.append(f"{var_name} = {result}")
        
        elif line.startswith("if"):
            if_tac, temp_var_count, label_count = handle_if_else(line, temp_var_count, label_count)
            tac.extend(if_tac)
        
        elif line.startswith("for"):
            loop_tac, temp_var_count, label_count = handle_loop(line, "for", temp_var_count, label_count)
            tac.extend(loop_tac)
        
        elif line.startswith("while"):
            loop_tac, temp_var_count, label_count = handle_loop(line, "while", temp_var_count, label_count)
            tac.extend(loop_tac)
        
        elif line.startswith("switch"):
            switch_tac, temp_var_count, label_count = handle_switch(line, temp_var_count, label_count)
            tac.extend(switch_tac)
        
        elif line.startswith("case"):
            case_tac, temp_var_count, label_count = handle_case(line, temp_var_count, label_count)
            tac.extend(case_tac)

        elif line.startswith("default"):
            default_tac = handle_default(label_count)
            tac.extend(default_tac)

        elif re.match(r'(\w+)\s*\((.*?)\);', line):
            function_call_tac, temp_var_count = handle_function_call(line, temp_var_count)
            tac.extend(function_call_tac)

    tac.append(f"L{label_count}:")
    tac.append("END")
    
    return tac

def read_c_code_from_file(file_path):
    with open(file_path, 'r') as file:
        c_code = file.read()
    return c_code

def write_tac_to_file(tac, output_file_path):
    with open(output_file_path, 'w') as file:
        for line in tac:
            file.write(line + '\n') 

input_file_path = "c_code.txt"
output_file_path = "c_code_output.txt"

c_code = read_c_code_from_file(input_file_path)
tac = generate_TAC_from_C_code(c_code)
write_tac_to_file(tac, output_file_path)

print(f"TAC has been written to {output_file_path}.")
