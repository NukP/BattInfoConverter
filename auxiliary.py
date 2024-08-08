import pandas as pd
import traceback
import inspect

def add_to_structure(jsonld, path, value, unit, data_container):
    from json_convert import get_information_value
    try:
        print('               ') # To add space between each Excel row - for debugging.
        current_level = jsonld
        unit_map = data_container.data['unit_map'].set_index('Item').to_dict(orient='index')
        context_connector = data_container.data['context_connector']
        connectors = set(context_connector['Item'])
        unique_id = data_container.data['unique_id']

        for idx, parts in enumerate(path):
            if len(parts.split('|')) == 1:
                part = parts
                special_command = None
                plf(value, part)
            elif len(parts.split('|')) == 2:
                special_command, part = parts.split('|')
                plf(value, part)
                if special_command == "rev":
                    plf(value, part)
                    if "@reverse" not in current_level:
                        plf(value, part)
                        current_level["@reverse"] = {}
                    current_level = current_level["@reverse"] ; plf(value, part)
            else:
                raise ValueError(f"Invalid JSON-LD at: {parts} in {path}")
            
            is_last = idx == len(path) - 1
            is_second_last = idx == len(path) - 2

            if part not in current_level:
                plf(value, part)
                if part in connectors:
                    plf(value, part)
                    connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0]
                    if pd.isna(connector_type):
                        plf(value, part)
                        current_level[part] = {}
                    else:
                        plf(value, part)
                        current_level[part] = {"@type": connector_type}
                else:
                    plf(value, part)
                    current_level[part] = {}
            
            #Handle the case of the single path.
            if len(path) == 1 and unit == 'No Unit':
                plf(value, part)
                if value in unique_id['Item'].values:
                    plf(value, part)
                    if "@type" in current_level:
                        plf(value, part)
                        if "@type" in current_level[part] and isinstance(current_level[part]["@type"], list):
                            plf(value, part)
                            if not pd.isna(value):
                                plf(value, part)
                                current_level[part]["@type"].append(value)
                        else:
                            plf(value, part)
                            if not pd.isna(value):
                                plf(value, part)
                                current_level[part]["@type"] = [value]
                    else:
                        plf(value, part)
                        if not pd.isna(value):
                            plf(value, part)
                            current_level[part]["@type"] = value
                else:
                    plf(value, part)
                    current_level[part]['rdfs:comment'] = value
                break

            if is_second_last and unit != 'No Unit':
                plf(value, part)
                if pd.isna(unit):
                    plf(value, part)
                    raise ValueError(f"The value '{value}' is filled in the wrong row, please check the schema")
                unit_info = unit_map[unit] ; plf(value, part)

                new_entry = {
                    "@type": path[-1],
                    "hasNumericalPart": {
                        "@type": "emmo:Real",
                        "hasNumericalValue": value
                    },
                    "hasMeasurementUnit": unit_info['Key']
                }
                
                # Check if the part already exists and should be a list
                if part in current_level:
                    plf(value, part)
                    if isinstance(current_level[part], list):
                        current_level[part].append(new_entry) ;plf(value, part)
                    else:
                        # Ensure we do not overwrite non-dictionary values
                        existing_entry = current_level[part] ;plf(value, part)
                        current_level[part] = [existing_entry, new_entry]
                else:
                    current_level[part] = [new_entry] ;plf(value, part)
                
                # Clean up any empty dictionaries in the list
                if isinstance(current_level[part], list):
                    current_level[part] = [item for item in current_level[part] if item != {}] ;plf(value, part)
                break

            if is_last and unit == 'No Unit':
                plf(value, part)
                if value in unique_id['Item'].values:
                    plf(value, part)
                    if "@type" in current_level:
                        plf(value, part)
                        if isinstance(current_level["@type"], list):
                            plf(value, part)
                            if not pd.isna(value):
                                current_level["@type"].append(value) ; plf(value, part)
                        else:
                            plf(value, part)
                            if not pd.isna(value):
                                current_level["@type"] = [current_level["@type"], value] ; plf(value, part)
                    else:
                        if not pd.isna(value):
                            current_level["@type"] = value ; plf(value, part)
                else:
                    current_level['rdfs:comment'] = value ; plf(value, part)
                break

            current_level = current_level[part]

            if not is_last and part in connectors:
                connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0] ; plf(value, part)
                if not pd.isna(connector_type):
                    plf(value, part)
                    if "@type" not in current_level:
                        current_level["@type"] = connector_type ; plf(value, part)
                    elif current_level["@type"] != connector_type:
                        plf(value, part)
                        if isinstance(current_level["@type"], list):
                            plf(value, part)
                            if connector_type not in current_level["@type"]:
                                current_level["@type"].append(connector_type) ; plf(value, part)
                        else:
                            current_level["@type"] = [current_level["@type"], connector_type] ; plf(value, part)

            if is_second_last and unit == 'No Unit':
                next_part = path[idx + 1] ; plf(value, part)
                if isinstance(current_level, dict): 
                    plf(value, part, current_level=current_level)
                    if next_part not in current_level:
                        current_level[next_part] = {} ; plf(value, part)
                    current_level = current_level[next_part]
                elif isinstance(current_level, list):
                    current_level.append({next_part: {}}) ; plf(value, part)
                    current_level = current_level[-1][next_part]

                if value in unique_id['Item'].values:
                    unique_id_of_value = get_information_value(unique_id, 'ID', value, "Item") ; plf(value, part)
                    if not pd.isna(unique_id_of_value):
                        current_level['@id'] = unique_id_of_value ; plf(value, part)
                    
                    if not pd.isna(value):
                        plf(value, part, current_level=current_level)
                        if "@type" in current_level:
                            plf(value, part)
                            if isinstance(current_level["@type"], list):
                                current_level["@type"].append(value) ; plf(value, part)
                            else:
                                current_level["@type"] = [current_level["@type"], value] ; plf(value, part)
                        else:
                            current_level["@type"] = value ; plf(value, part)
                else:
                    current_level['rdfs:comment'] = value ; plf(value, part)
                break

    except Exception as e:
        traceback.print_exc()  # Print the full traceback
        raise RuntimeError(f"Error occurred with value '{value}' and path '{path}': {str(e)}")


def plf(value, part, current_level = None, debug_switch = True):
    """Print Line Function.
    This function is used for debugging.
    """
    if debug_switch:
        current_frame = inspect.currentframe()
        line_number = current_frame.f_back.f_lineno
        if current_level is not None:
            print(f'pass line {line_number}, value:', value,'AND part:', part, 'AND current_level:', current_level)
        else:
            print(f'pass line {line_number}, value:', value,'AND part:', part)
    else:
        pass 

