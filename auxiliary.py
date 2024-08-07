import pandas as pd
import traceback
import inspect

def add_to_structure(jsonld, path, value, unit, data_container):
    from json_convert import get_information_value
    try:
        current_level = jsonld
        unit_map = data_container.data['unit_map'].set_index('Item').to_dict(orient='index')
        context_connector = data_container.data['context_connector']
        connectors = set(context_connector['Item'])
        unique_id = data_container.data['unique_id']

        for idx, part in enumerate(path):
            is_last = idx == len(path) - 1
            is_second_last = idx == len(path) - 2

            if part not in current_level:
                plf(value)
                if part in connectors:
                    plf(value)
                    connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0]
                    if pd.isna(connector_type):
                        plf(value)
                        current_level[part] = {}
                    else:
                        plf(value)
                        current_level[part] = {"@type": connector_type}
                else:
                    plf(value)
                    current_level[part] = {}
            
            #Handle the case of the single path.
            if len(path) == 1 and unit == 'No Unit':
                plf(value)
                if value in unique_id['Item'].values:
                    plf(value)
                    if "@type" in current_level:
                        plf(value)
                        if "@type" in current_level[part] and isinstance(current_level[part]["@type"], list):
                            plf(value)
                            if not pd.isna(value):
                                plf(value)
                                current_level[part]["@type"].append(value)
                        else:
                            plf(value)
                            if not pd.isna(value):
                                plf(value)
                                current_level[part]["@type"] = [value]
                    else:
                        plf(value)
                        if not pd.isna(value):
                            plf(value)
                            current_level[part]["@type"] = value
                else:
                    plf(value)
                    current_level[part]['rdfs:comment'] = value
                break

            if is_second_last and unit != 'No Unit':
                plf(value)
                if pd.isna(unit):
                    plf(value)
                    raise ValueError(f"The value '{value}' is filled in the wrong row, please check the schema")
                unit_info = unit_map[unit] ; plf(value)

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
                    plf(value)
                    if isinstance(current_level[part], list):
                        current_level[part].append(new_entry) ;plf(value)
                    else:
                        # Ensure we do not overwrite non-dictionary values
                        existing_entry = current_level[part] ;plf(value)
                        current_level[part] = [existing_entry, new_entry]
                else:
                    current_level[part] = [new_entry] ;plf(value)
                
                # Clean up any empty dictionaries in the list
                if isinstance(current_level[part], list):
                    current_level[part] = [item for item in current_level[part] if item != {}] ;plf(value)
                break

            if is_last and unit == 'No Unit':
                plf(value)
                if value in unique_id['Item'].values:
                    plf(value)
                    if "@type" in current_level:
                        plf(value)
                        if isinstance(current_level["@type"], list):
                            plf(value)
                            if not pd.isna(value):
                                current_level["@type"].append(value) ; plf(value)
                        else:
                            plf(value)
                            if not pd.isna(value):
                                current_level["@type"] = [current_level["@type"], value] ; plf(value)
                    else:
                        if not pd.isna(value):
                            current_level["@type"] = value ; plf(value)
                else:
                    current_level['rdfs:comment'] = value ; plf(value)
                break

            current_level = current_level[part]

            if not is_last and part in connectors:
                connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0] ; plf(value)
                if not pd.isna(connector_type):
                    plf(value)
                    if "@type" not in current_level:
                        current_level["@type"] = connector_type ; plf(value)
                    elif current_level["@type"] != connector_type:
                        plf(value)
                        if isinstance(current_level["@type"], list):
                            plf(value)
                            if connector_type not in current_level["@type"]:
                                current_level["@type"].append(connector_type) ; plf(value)
                        else:
                            current_level["@type"] = [current_level["@type"], connector_type] ; plf(value)

            if is_second_last and unit == 'No Unit':
                next_part = path[idx + 1] ; plf(value)
                if isinstance(current_level, dict): 
                    plf(value)
                    if next_part not in current_level:
                        current_level[next_part] = {} ; plf(value)
                    current_level = current_level[next_part]
                elif isinstance(current_level, list):
                    current_level.append({next_part: {}}) ; plf(value)
                    current_level = current_level[-1][next_part]

                if value in unique_id['Item'].values:
                    unique_id_of_value = get_information_value(unique_id, 'ID', value, "Item") ; plf(value)
                    if not pd.isna(unique_id_of_value):
                        current_level['@id'] = unique_id_of_value ; plf(value)
                    
                    if not pd.isna(value):
                        plf(value)
                        if "@type" in current_level:
                            plf(value)
                            if isinstance(current_level["@type"], list):
                                current_level["@type"].append(value) ; plf(value)
                            else:
                                current_level["@type"] = [current_level["@type"], value] ; plf(value)
                        else:
                            current_level["@type"] = value ; plf(value)
                else:
                    current_level['rdfs:comment'] = value ; plf(value)
                break

    except Exception as e:
        traceback.print_exc()  # Print the full traceback
        raise RuntimeError(f"Error occurred with value '{value}' and path '{path}': {str(e)}")
    
def plf(value, current_level_part = None):
    current_frame = inspect.currentframe()
    line_number = current_frame.f_back.f_lineno
    if current_level_part is not None:
        print(f'pass line {line_number}, value:', value,'AND current_level_part:', current_level_part)
    else:
        print(f'pass line {line_number}, value:', value)
