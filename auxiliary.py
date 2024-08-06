import pandas as pd
import traceback

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
                if part in connectors:
                    connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0]
                    if pd.isna(connector_type):
                        current_level[part] = {}
                    else:
                        current_level[part] = {"@type": connector_type}
                else:
                    current_level[part] = {}
            
            #Handle the case of the single path.
            if len(path) == 1 and unit == 'No Unit':
                print('Pass line 28, vakue: ', value)
                if value in unique_id['Item'].values:
                    if "@type" in current_level:
                        if isinstance(current_level["@type"], list):
                            if not pd.isna(value):
                                current_level[part]["@type"].append(value)
                        else:
                            if not pd.isna(value):
                                current_level[part]["@type"] = [current_level["@type"], value]
                    else:
                        if not pd.isna(value):
                            current_level[part]["@type"] = value
                else:
                    current_level[part]['rdfs:comment'] = value
                break

            if is_second_last and unit != 'No Unit':
                if pd.isna(unit):
                    raise ValueError(f"The value '{value}' is filled in the wrong row, please check the schema")
                unit_info = unit_map[unit]

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
                    if isinstance(current_level[part], list):
                        current_level[part].append(new_entry)
                    else:
                        # Ensure we do not overwrite non-dictionary values
                        existing_entry = current_level[part]
                        current_level[part] = [existing_entry, new_entry]
                else:
                    current_level[part] = [new_entry]
                
                # Clean up any empty dictionaries in the list
                if isinstance(current_level[part], list):
                    current_level[part] = [item for item in current_level[part] if item != {}]
                break

            if is_last and unit == 'No Unit':
                if value in unique_id['Item'].values:
                    if "@type" in current_level:
                        if isinstance(current_level["@type"], list):
                            if not pd.isna(value):
                                current_level["@type"].append(value)
                        else:
                            if not pd.isna(value):
                                current_level["@type"] = [current_level["@type"], value]
                    else:
                        if not pd.isna(value):
                            current_level["@type"] = value
                else:
                    current_level['rdfs:comment'] = value
                break

            current_level = current_level[part]

            if not is_last and part in connectors:
                connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0]
                if not pd.isna(connector_type):
                    if "@type" not in current_level:
                        current_level["@type"] = connector_type
                    elif current_level["@type"] != connector_type:
                        if isinstance(current_level["@type"], list):
                            if connector_type not in current_level["@type"]:
                                current_level["@type"].append(connector_type)
                        else:
                            current_level["@type"] = [current_level["@type"], connector_type]

            if is_second_last and unit == 'No Unit':
                next_part = path[idx + 1]
                if next_part not in current_level:
                    current_level[next_part] = {}
                current_level = current_level[next_part]
                if value in unique_id['Item'].values:
                    unique_id_of_value = get_information_value(unique_id, 'ID', value, "Item")
                    if not pd.isna(unique_id_of_value):
                        current_level['@id'] = unique_id_of_value
                    if "@type" in current_level:
                        if isinstance(current_level["@type"], list):
                            if not pd.isna(value):
                                current_level["@type"].append(value)
                        else:
                            if not pd.isna(value):
                                current_level["@type"] = [current_level["@type"], value]
                    else:
                        if not context_connector[context_connector['Item'] == next_part].empty:
                            connector_type = context_connector.loc[context_connector['Item'] == next_part, 'Key'].values[0]
                            if not pd.isna(connector_type):
                                current_level["@type"] = [value, connector_type]
                            else:
                                current_level["@type"] = value
                        else:
                            current_level["@type"] = value
                else:
                    current_level['rdfs:comment'] = value
                break
    except Exception as e:
        traceback.print_exc()  # Print the full traceback
        raise RuntimeError(f"Error occurred with value '{value}' and path '{path}': {str(e)}")
