import pandas as pd

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

            print(f'Current level: {current_level}')  # Debugging line
            print(f'Part: {part}')  # Debugging line

            if isinstance(current_level, list):
                found = False
                for item in current_level:
                    if isinstance(item, dict) and part in item:
                        current_level = item[part]
                        found = True
                        break
                if not found:
                    new_entry = {part: {}}
                    current_level.append(new_entry)
                    current_level = new_entry[part]
            else:
                if part not in current_level:
                    if part in connectors:
                        connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0]
                        if pd.isna(connector_type):
                            current_level[part] = {}
                        else:
                            current_level[part] = {"@type": connector_type}
                    else:
                        current_level[part] = {}

                current_level = current_level[part]

            if is_second_last:
                if 'hasNumericalPart' in path or (unit != 'No Unit' and not pd.isna(unit)):
                    # Logic for adding numerical part
                    new_entry = {
                        "@type": path[-1],
                        "hasNumericalPart": {
                            "@type": "emmo:Real",
                            "hasNumericalValue": value
                        }
                    }
                    if unit != 'No Unit' and not pd.isna(unit):
                        unit_info = unit_map[unit]
                        new_entry["hasMeasurementUnit"] = unit_info['Key']

                    print(f'New entry (numerical): {new_entry}')  # Debugging line

                    if part in current_level:
                        if isinstance(current_level[part], list):
                            current_level[part].append(new_entry)
                        else:
                            existing_entry = current_level[part]
                            current_level[part] = [existing_entry, new_entry]
                    else:
                        current_level[part] = [new_entry]
                else:
                    # Logic for adding non-numerical parts
                    new_entry = {"@type": path[-1], "value": value}
                    print(f'New entry (non-numerical): {new_entry}')  # Debugging line

                    if part in current_level:
                        if isinstance(current_level[part], list):
                            current_level[part].append(new_entry)
                        else:
                            existing_entry = current_level[part]
                            current_level[part] = [existing_entry, new_entry]
                    else:
                        current_level[part] = [new_entry]

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
        print(f'Error details: current_level={current_level}, part={part}, path={path}')  # Debugging line
        raise RuntimeError(f"Error occurred with value '{value}' and path '{path}': {str(e)}")
