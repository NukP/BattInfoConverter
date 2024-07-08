import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO

# Define the version of the app
APP_VERSION = "0.2.0"


markdown_content = """ 
Ontologizing your metadata can significantly enhance the interoperability of data across various research groups.
To learn more about ontologizing your metadata, we invite you to visit our page on
[ontologizing metadata](https://github.com/ord-premise/interoperability-guidelines/tree/main). 
While the benefits of this process are clear, it can often be a daunting task in practice. 
With this in mind, we've developed an BattINFO converter web application designed to streamline and expedite this intricate task,
making it more manageable for you and your team.

BattINFO converter helps you ontologize metadata for coin cell battery based on [BattINFO](https://big-map.github.io/BattINFO/index.html) ontology. 

## Excel metadata files
Here you will find an Excel file template that you can fill out with your metadata. We will add more template for other cell types in the future. Be sure to check out!
### Blank Excel metadata file
[Coin cell battery schema version 0.1.0](https://raw.githubusercontent.com/NukP/xls_convert/fix_oslo2/Excel%20for%20reference/CoinCellBattery_Schemas_version_010.xlsx) 
### Example filled out Excel metadata file
[Example-filled Coin cell battery schema version 0.1.0](https://raw.githubusercontent.com/NukP/xls_convert/fix_oslo2/Excel%20for%20reference/Example_CoinCellBattery_Schemas_version_010.xlsx)

 ## How to Fill Out the Excel metadata file

1. **Essential Tabs**: The Excel file should contain the following essential tabs: `Schema`, `Ontology - Item`, `@context-TopLevel`, and `Ontology - Unit`. These tabs are crucial for the functioning of the web app. Do not change their names.  
2. **First Row**: Ensure that the first row of each tab contains the column names. These names are used as references by the app.  
3. **Filling Data**: In the `Schema` tab, fill in the following columns:  
    - **Value**: Enter the metadata value. If the cell is empty, the script will skip this metadata item.  
    - **Unit**: Specify the unit of the metadata. If the metadata item doesn't require a unit, enter "No Unit". Leaving this cell empty will cause an error.  
    - **Ontology link**: Provide the ontology link. If you do not want to ontologize a particular row, enter "NotOntologize". To add a comment instead, enter "Comment".  

## How to adapt the Excel metadata file for your own custom data


1. **Adding New Ontology Terms**:
    - Go to the website providing the ontology concept (e.g., BattInfo, Schema.org).
    - In the `@context-TopLevel` tab, add the top-level URL of the ontology website.
    - In the `Ontology - Item` tab, define the new ontology term. Use the `Item` column for the term and the `Key` column for the ontology reference (e.g., `schemas:identifier`).

2. **Adding New Units**:
    - In the `Ontology - Unit` tab, define the new unit. Include the `Item`, `Label`, and `Symbol` columns, along with the ontology reference in the `Key` column.

3. **Adding New Rows**:  
    - Add new rows to the `Schema` tab (or remove existing rows) to include additional metadata items. Ensure that the `Ontology link` column references the new ontology terms and units.

# Acknowledgement 
BattINFO converter web application was developed at [Empa](https://www.empa.ch/), Swiss Federal Laboratories for Materials Science and Technology in [Material for Energy Conversion lab](https://www.empa.ch/web/s501).  


We acknowledge stimulating discussions and support from Dr Simon Clark, SINTEF, Norway.


This work has been developed under the following project and funding agencies: 
- [PREMISE](https://ord-premise.org/)  
  
- [Battery 2030+](https://battery2030.eu/)

- [Big-Map project](https://www.big-map.eu/)


"""

image_url = 'https://raw.githubusercontent.com/NukP/xls_convert/fix_oslo2/BattInfoCOnverter.png'

def get_information_value(row_name, df, col_locator='Item'):
    """
    Return the value of a column "Key" at the row where the column "Item" is equal to row_name
    """
    return df.loc[df[col_locator] == row_name, 'Key'].values[0]

def convert_excel_to_jsonld(excel_file):
    excel_data = pd.ExcelFile(excel_file)
    
    schema = pd.read_excel(excel_data, 'Schema')
    item_map = pd.read_excel(excel_data, 'Ontology - Item').set_index('Item').to_dict(orient='index')
    unit_map = pd.read_excel(excel_data, 'Ontology - Unit').set_index('Item').to_dict(orient='index')
    context_toplevel = pd.read_excel(excel_data, '@context-TopLevel')
    context_connector = pd.read_excel(excel_data, '@context-Connector')
    info = pd.read_excel(excel_data, 'JSON - Info')

    print("Data loaded from Excel:")
    print(f"Schema: {schema.head()}")
    print(f"Item map: {item_map}")
    print(f"Unit map: {unit_map}")
    print(f"Context top level: {context_toplevel}")
    print(f"Context connector: {context_connector}")
    print(f"Info: {info}")

    jsonld_output = create_jsonld_with_conditions(schema, info, item_map, unit_map, context_toplevel, context_connector)
    
    return jsonld_output

def create_jsonld_with_conditions(schema, info, item_map, unit_map, context_toplevel, context_connector):
    jsonld = {
        "@context": ["https://w3id.org/emmo/domain/battery/context", {}],
        "@type": get_information_value(row_name='Cell type', df=info),
        "schema:version": get_information_value(row_name='BattINFO CoinCellSchema version', df=info),
        "schemas:productID": get_information_value(row_name='Cell ID', df=info),
        "schemas:dateCreated": str(get_information_value(row_name='Date of cell assembly', df=info)),
        "rdfs:comment": {} 
    }

    print(f"Initial JSON-LD: {jsonld}")

    # Build the @context part
    for _, row in context_toplevel.iterrows():
        jsonld["@context"][1][row['Item']] = row['Key']
    
    print(f"Updated @context: {jsonld['@context']}")

    connectors = set()
    for _, row in context_connector.iterrows():
        connectors.add(row['Item'])  # Track connectors to avoid redefining types

    # Process each schema entry to construct the JSON-LD output
    for _, row in schema.iterrows():
        print(f"Processing row: {row}")
        if pd.isna(row['Value']) or row['Ontology link'] == 'NotOntologize':
            continue
        if row['Ontology link'] == 'Comment':
            jsonld["rdfs:comment"][row['Metadata']] = row['Value']
            continue
        if pd.isna(row['Unit']):
            raise ValueError(f"The value '{row['Value']}' is filled in the wrong row, please check the schema")

        ontology_path = row['Ontology link'].split('-')
        print(f"Ontology path: {ontology_path}")
        add_to_structure(jsonld, ontology_path, row['Value'], row['Unit'], connectors, item_map, unit_map, context_connector)

    # Add the BattInfoConverter version comment
    jsonld["rdfs:comment"]["BattINFO Converter version"] = APP_VERSION

    print(f"Final JSON-LD: {jsonld}")

    return jsonld

def add_to_structure(jsonld, path, value, unit, connectors, item_map, unit_map, context_connector):
    current_level = jsonld
    print(f"Initial jsonld: {jsonld}")
    # Iterate through the path to create or navigate the structure
    for idx, part in enumerate(path):
        is_last = idx == len(path) - 1  # Check if current part is the last in the path

        print(f"Current part: {part}")
        if part not in current_level:
            if part in connectors:
                # Assign the default @type for non-terminal connectors
                connector_type = context_connector.loc[context_connector['Item'] == part, 'Key'].values[0]
                if pd.isna(connector_type):
                    connector_type = item_map[path[-1]]['Key']
                current_level[part] = {"@type": connector_type}
            else:
                if part in item_map:
                    current_level[part] = {"@type": item_map[part]['Key']}
                else:
                    raise ValueError(f"Connector or item '{part}' is not defined in any relevant sheet.")
            print(f"Updated current_level[{part}]: {current_level[part]}")

        if not is_last:
            current_level = current_level[part]
            print(f"Navigating to the next level: {current_level}")
        else:
            # Handle the unit and value structure for the last item
            if unit != 'No Unit':
                if pd.isna(unit):
                    raise ValueError(f"The value '{value}' is filled in the wrong row, please check the schema")
                unit_info = unit_map[unit]
                current_level[part] = {
                    "@type": item_map[part]['Key'],
                    "hasNumericalPart": {
                        "@type": "emmo:Real",
                        "hasNumericalValue": value
                    },
                    "hasMeasurementUnit": unit_info['Key']
                }
            else:
                if "@type" in current_level[part]:
                    if isinstance(current_level[part]["@type"], list):
                        current_level[part]["@type"].append(value)
                    else:
                        current_level[part]["@type"] = [current_level[part]["@type"], value]
                else:
                    current_level[part]["@type"] = value
            print(f"Final current_level[{part}]: {current_level[part]}")
    print(f"Final jsonld: {jsonld}")



def main():
    st.image(image_url)
    
    st.markdown(f"__App Version: {APP_VERSION}__")
    
    uploaded_file = st.file_uploader("__Upload your metadata Excel file here__", type=['xlsx', 'xlsm'])
    
    if uploaded_file is not None:
        # Extract the base name of the file (without the extension)
        base_name = os.path.splitext(uploaded_file.name)[0]
        
        # Convert the uploaded Excel file to JSON-LD
        jsonld_output = convert_excel_to_jsonld(uploaded_file)
        jsonld_str = json.dumps(jsonld_output, indent=4)

        # Download button
        to_download = BytesIO(jsonld_str.encode())
        output_file_name = f"BattINFO_converter_{base_name}.json"  
        st.download_button(label="Download JSON-LD",
                        data=to_download,
                        file_name=output_file_name,
                        mime="application/json")
        
        # Convert JSON-LD output to a string to display in text area (for preview)
        st.text_area("JSON-LD Output", jsonld_str, height=300)
    
    st.markdown(markdown_content, unsafe_allow_html=True)
    st.image('https://raw.githubusercontent.com/NukP/xls_convert/fix_oslo2/sponsor.png', width=700)

if __name__ == "__main__":
    main()

