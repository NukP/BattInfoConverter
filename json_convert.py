from dataclasses import dataclass, field
import pandas as pd

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

def get_information_value(row_name, df, col_locator='Item'):
    """
    Return the value of a column "Key" at the row where the column "Item" is equal to row_name
    """
    return df.loc[df[col_locator] == row_name, 'Key'].values[0]

def add_to_structure(jsonld, path, value, unit, data_container):
    current_level = jsonld
    unit_map = data_container.data['unit_map'].set_index('Item').to_dict(orient='index')
    context_connector = data_container.data['context_connector']
    connectors = set(context_connector['Item'])

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

        # Handle the last item normally when unit is "No Unit"
        if is_last and unit == 'No Unit':
            if "@type" in current_level:
                if isinstance(current_level["@type"], list):
                    current_level["@type"].append(value)
                else:
                    current_level["@type"] = [current_level["@type"], value]
            else:
                current_level["@type"] = value
            break

        # Move to the next level in the path
        current_level = current_level[part]

        # Ensure @type is set correctly for non-terminal connectors
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

        # Handle the unit and value structure for the last item when unit is "No Unit"
        if is_second_last and unit == 'No Unit':
            next_part = path[idx + 1]
            if next_part not in current_level:
                current_level[next_part] = {}
            current_level = current_level[next_part]
            if "@type" in current_level:
                if isinstance(current_level["@type"], list):
                    current_level["@type"].append(value)
                else:
                    current_level["@type"] = [current_level["@type"], value]
            else:
                current_level["@type"] = value
            break

def create_jsonld_with_conditions(data_container: ExcelContainer):
    schema = data_container.data['schema']
    info = data_container.data['info']
    context_toplevel = data_container.data['context_toplevel']
    context_connector = data_container.data['context_connector']

    jsonld = {
        "@context": ["https://w3id.org/emmo/domain/battery/context", {}],
        "@type": get_information_value(row_name='Cell type', df=info),
        "schema:version": get_information_value(row_name='BattINFO CoinCellSchema version', df=info),
        "schemas:productID": get_information_value(row_name='Cell ID', df=info),
        "schemas:dateCreated": str(get_information_value(row_name='Date of cell assembly', df=info)),
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
    # Create an instance of ExcelContainer
    data_container = ExcelContainer(excel_file)

    # Generate JSON-LD using the data container
    jsonld_output = create_jsonld_with_conditions(data_container)

    return jsonld_output