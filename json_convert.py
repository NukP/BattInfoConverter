from dataclasses import dataclass, field
import pandas as pd
import streamlit as st

APP_VERSION = "0.4.0"

@dataclass
class ExcelContainer:
    excel_file: str
    data: dict = field(init=False)

    def __post_init__(self):
        excel_data = pd.ExcelFile(self.excel_file)
        self.data = {
            "schema": pd.read_excel(excel_data, 'Schema'),
            "unit_map": pd.read_excel(excel_data, 'Ontology - Unit'),
            "context_toplevel": pd.read_excel(excel_data, '@context-TopLevel'),
            "context_connector": pd.read_excel(excel_data, '@context-Connector'),
            "info": pd.read_excel(excel_data, 'JSON - Info'),
            "unique_id": pd.read_excel(excel_data, 'Unique ID')
        }

def get_information_value(df, col_to_look, row_to_look, col_to_match):
    """
    Return the value of a column "col_to_look" at the row where the column "col_to_match" is equal to row_to_look.
    If no match is found, return None.
    """
    result = df.query(f"{col_to_match} == @row_to_look")[col_to_look]
    return result.iloc[0] if not result.empty else None

def add_to_structure(jsonld, path, value, unit, data_container):
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

                if part in current_level:
                    if isinstance(current_level[part], list):
                        current_level[part].append(new_entry)
                    else:
                        existing_entry = current_level[part]
                        current_level[part] = [existing_entry, new_entry]
                else:
                    current_level[part] = [new_entry]

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
        raise RuntimeError(f"Error occurred with value '{value}' and path '{path}': {str(e)}")

def create_jsonld_with_conditions(data_container: ExcelContainer):
    schema = data_container.data['schema']
    info = data_container.data['info']
    context_toplevel = data_container.data['context_toplevel']
    context_connector = data_container.data['context_connector']

    jsonld = {
        "@context": ["https://w3id.org/emmo/domain/battery/context", {}],
        "@type": get_information_value(df=info, col_to_look='Key', row_to_look='Cell type', col_to_match='Item'),
        "schema:version": get_information_value(df=info, col_to_look='Key', row_to_look='BattINFO CoinCellSchema version', col_to_match='Item'),
        "schemas:productID": get_information_value(df=info, col_to_look='Key', row_to_look='Cell ID', col_to_match='Item'),
        "schemas:dateCreated": str(get_information_value(df=info, col_to_look='Key', row_to_look='Date of cell assembly', col_to_match='Item')),
        "rdfs:comment": {}
    }

    for _, row in context_toplevel.iterrows():
        jsonld["@context"][1][row['Item']] = row['Key']

    connectors = set(context_connector['Item'])

    for _, row in schema.iterrows():
        if pd.isna(row['Value']) or row['Ontology link'] == 'NotOntologize':
            continue
        if row['Ontology link'] == 'Comment':
            jsonld["rdfs:comment"][row['Metadata']] = row['Value']
            continue
        if pd.isna(row['Unit']):
            raise ValueError(f"The value '{row['Value']}' is filled in the wrong row, please check the schema")

        ontology_path = row['Ontology link'].split('-')
        add_to_structure(jsonld, ontology_path, row['Value'], row['Unit'], data_container)
    jsonld["rdfs:comment"]["BattINFO Converter version"] = APP_VERSION

    return jsonld

def convert_excel_to_jsonld(excel_file):
    #print('Converting new Excel file')
    #print('\n')
    # Create an instance of ExcelContainer
    data_container = ExcelContainer(excel_file)

    # Generate JSON-LD using the data container
    jsonld_output = create_jsonld_with_conditions(data_container)

    return jsonld_output