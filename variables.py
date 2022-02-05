def set_empty_to_none(variable_dict):
    for key in variable_dict.keys():
        if variable_dict[key] == '':
            variable_dict[key] = None
    return variable_dict