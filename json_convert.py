from dataclasses import dataclass, field
import pandas as pd
import streamlit as st

APP_VERSION = "0.3.0"

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
    current_level = jsonld
    unit_map = data_container.data['unit_map'].set_index('Item').to_dict(orient='index')
    context_connector = data_container.data['context_connector']
    connectors = set(context_connector['Item'])
    unique_id = data_container.data['unique_id']


    # Iterate through the path to create or navigate the structure
    for idx, part in enumerate(path):
        is_last = idx == len(path) - 1  # Check if current part is the last in the path
        is_second_last = idx == len(path) - 2  # Check if current part is the second last in the path

        # Initialize the current part if it doesn't exist
        if part not in current_level:
            if part in connectors:
                # Assign the default @type for non-terminal connectors
                connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0]
                if pd.isna(connector_type):
                    current_level[part] = {}
                else:
                    current_level[part] = {"@type": connector_type}
            else:
                current_level[part] = {}

        # Handle the unit and value structure for the second last item only when unit is not "No Unit"
        if is_second_last and unit != 'No Unit':
            print(f"pass the 56 loop, value: {value}, part: {part}")
            if pd.isna(unit):
                raise ValueError(f"The value '{value}' is filled in the wrong row, please check the schema")
            unit_info = unit_map[unit]
            current_level[part] = {
                "@type": path[-1],
                "hasNumericalPart": {
                    "@type": "emmo:Real",
                    "hasNumericalValue": value
                },
                "hasMeasurementUnit": unit_info['Key']
            }
            break

        # Handle the last item normally when unit is "No Unit" -- Fix here for the issue with unique id
        if is_last and unit == 'No Unit':
            print(f"pass the 72 loop, value: {value}, part: {part}")
            if value in unique_id['Item'].values:
                print(f'The value {value} is in unique id')
                if "@type" in current_level:
                    if isinstance(current_level["@type"], list):
                        current_level["@type"].append(value)
                    else:
                        current_level["@type"] = [current_level["@type"], value]
                else:
                    current_level["@type"] = value
            else:
                current_level['rdfs:comment'] = value
            break

        # Move to the next level in the path
        current_level = current_level[part]

        # Ensure @type is set correctly for non-terminal connectors
        if not is_last and part in connectors:
            print(f'pass the 90 loop, value: {value}, part: {part}')
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


        # Handle the unit and value structure for the last item when unit is "No Unit"
        if is_second_last and unit == 'No Unit':
            print(f'pass the 104 loop, value: {value}, part: {part}')
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
                        current_level["@type"].append(value)
                    else:
                        current_level["@type"] = [current_level["@type"], value]
                else:
                    current_level["@type"] = value
            else:
                current_level['rdfs:comment'] = value
            break

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
    print('Converting new Excel file')
    print('\n')
    # Create an instance of ExcelContainer
    data_container = ExcelContainer(excel_file)

    # Generate JSON-LD using the data container
    jsonld_output = create_jsonld_with_conditions(data_container)

    return jsonld_output