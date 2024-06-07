import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO
import logging

# Define the version of the app
APP_VERSION = "1.0.0"

# Setup logging
logging.basicConfig(filename='usage.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

markdown_content = """ 
Ontologizing your metadata can significantly enhance the interoperability of data across various research groups.
To learn more about ontologizing your metadata, we invite you to visit our page on
[ontologizing metadata](https://github.com/ord-premise/interoperability-guidelines/tree/main). 
While the benefits of this process are clear, it can often be a daunting task in practice. 
With this in mind, we've developed an BattINFO converter web application designed to streamline and expedite this intricate task,
making it more manageable for you and your team.

BattINFO converter helps you ontologize metadata for coin cell battery based on [BattINFO](https://big-map.github.io/BattINFO/index.html) ontology. 

# Usage
To use our Excel to JSON-LD converter, fill out the [metadata Excel file](https://drive.switch.ch/index.php/s/CNav0yDkRgg2KOZ) in the specified value column.
It is perfectly acceptable if not all rows are filled in; leaving some rows empty does not affect the script's operation.
Simply upload the filled Excel metadata file and our BattINFO converter will convert it into JSON-LD file.

# Acknowledgement 
BattINFO converter web application was developed at Empa, Swiss Federal Laboratories for Materials Science and Technology, Material for Energy Conversion lab.


This work has been developed under the following project and funding agencies: 
- [PREMISE](https://github.com/ord-premise)  
  
- [Battery 2030+](https://battery2030.eu/)  


"""

image_url = 'https://drive.switch.ch/index.php/apps/files_sharing/ajax/publicpreview.php?x=2888&y=920&a=true&file=BattINFO%2520converter%2520logo.PNG&t=bxd8AZRM6CDTFeM&scalingup=0'

def create_jsonld_with_conditions(schemas, item_map, unit_map, context_toplevel, context_connector):
    jsonld = {
        "@context": {},
        "Battery": {
            "@type": "battery:Battery"
        }
    }

    # Build the @context part
    for _, row in context_toplevel.iterrows():
        jsonld["@context"][row['Item']] = row['Key']
    
    connectors = set()
    for _, row in context_connector.iterrows():
        jsonld["@context"][row['Item']] = row['Key']
        connectors.add(row['Item'])  # Track connectors to avoid redefining types

    # Helper function to add nested structures with type annotations
    def add_to_structure(path, value, unit):
        current_level = jsonld["Battery"]
        # Iterate through the path to create or navigate the structure
        for idx, part in enumerate(path[1:]):
            is_last = idx == len(path) - 2  # Check if current part is the last in the path

            if part not in current_level:
                if part in connectors:
                    current_level[part] = {}
                else:
                    if part in item_map:
                        current_level[part] = {"@type": item_map[part]['Key']}
                    else:
                        raise ValueError(f"Connector or item '{part}' is not defined in any relevant sheet.")

            if not is_last:
                current_level = current_level[part]
            else:
                # Handle the unit and value structure for the last item
                final_type = item_map.get(part, {}).get('Key', '')
                if unit != 'No Unit':
                    if pd.isna(unit):
                        raise ValueError(f"The value '{value}' is filled in the wrong row, please check the schemas")
                    unit_info = unit_map[unit]
                    current_level[part] = {
                        "@type": final_type,
                        "hasNumberValue": {
                            "@type": "emmo:hasNumberValue",
                            "value": value,
                            "unit": {
                                "label": unit_info['Label'],
                                "symbol": unit_info['Symbol'],
                                "@type": unit_info['Key']
                            }
                        }
                    }
                else:
                    current_level[part] = {
                        "@type": final_type,
                        "value": value
                    }

    # Process each schema entry to construct the JSON-LD output
    for _, row in schemas.iterrows():
        if pd.isna(row['Value']) or row['Ontology link'] == 'NotOntologize':
            continue
        if pd.isna(row['Unit']):
            raise ValueError(f"The value '{row['Value']}' is filled in the wrong row, please check the schemas")

        ontology_path = row['Ontology link'].split('-')
        add_to_structure(ontology_path, row['Value'], row['Unit'])

    return jsonld

def convert_excel_to_jsonld(excel_file):
    excel_data = pd.ExcelFile(excel_file)
    
    schemas = pd.read_excel(excel_data, 'Schemas')
    item_map = pd.read_excel(excel_data, 'Ontology - Item').set_index('Item').to_dict(orient='index')
    unit_map = pd.read_excel(excel_data, 'Ontology - Unit').set_index('Item').to_dict(orient='index')
    context_toplevel = pd.read_excel(excel_data, '@context-TopLevel')
    context_connector = pd.read_excel(excel_data, '@context-Connector')

    jsonld_output = create_jsonld_with_conditions(schemas, item_map, unit_map, context_toplevel, context_connector)
    
    return jsonld_output

def main():
    st.image(image_url)
    
    st.markdown(f"### App Version: {APP_VERSION}")
    
    uploaded_file = st.file_uploader("Upload your metadata Excel file here", type=['xlsx', 'xlsm'])
    
    if uploaded_file is not None:
        # Extract the base name of the file (without the extension)
        base_name = os.path.splitext(uploaded_file.name)[0]
        
        # Convert the uploaded Excel file to JSON-LD
        jsonld_output = convert_excel_to_jsonld(uploaded_file)
        jsonld_str = json.dumps(jsonld_output, indent=4)
        
        # Log the usage
        logging.info(f"File uploaded: {uploaded_file.name}, converted successfully.")

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
    st.image('https://drive.switch.ch/index.php/apps/files_sharing/ajax/publicpreview.php?x=2888&y=920&a=true&file=Funders.PNG&t=lgmDOqzgpyFi5Gh&scalingup=0', width=700)


if __name__ == "__main__":
    main()
