import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO

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
        "Battery": {}
    }

    # Build the @context part
    for _, row in context_toplevel.iterrows():
        jsonld["@context"][row['Item']] = row['Key']
    
    for _, row in context_connector.iterrows():
        jsonld["@context"][row['Item']] = row['Key']

    # A helper function to add nested structures
    def add_to_structure(path, value, unit):
        current_level = jsonld["Battery"]
        # Start directly from the second item in the path (after Battery)
        for part in path[1:-1]: 
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        
        final_part = path[-1]
        # Determine if the final_part is a connector or an item
        if final_part in jsonld["@context"]:
            item_type = jsonld["@context"][final_part]
        else:
            item_type = item_map.get(final_part, {}).get('Key', '')

        # Handle the unit and value structure
        if unit != 'No Unit':
            unit_info = unit_map[unit]
            current_level[final_part] = {
                "@type": item_type,
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
            current_level[final_part] = {
                "@type": item_type,
                "value": value
            }

    # Build the Battery part using schemas
    for _, row in schemas.iterrows():
        if pd.isna(row['Value']) or row['Ontology link'] == 'NotOntologize':
            continue
        
        ontology_path = row['Ontology link'].split('-')
        add_to_structure(ontology_path, row['Value'], row['Unit'])

    return jsonld

def convert_excel_to_jsonld(excel_file):
    excel_data = pd.ExcelFile(excel_file)
    
    schemas = pd.read_excel(excel_data, sheet_name='Schemas')
    item_map = pd.read_excel(excel_data, sheet_name='Ontology - Item').set_index('Item').to_dict(orient='index')
    unit_map = pd.read_excel(excel_data, sheet_name='Ontology - Unit').set_index('Item').to_dict(orient='index')
    context_toplevel = pd.read_excel(excel_data, sheet_name='@context-TopLevel')
    context_connector = pd.read_excel(excel_data, sheet_name='@context-Connector')

    jsonld_output = create_jsonld_with_conditions(schemas, item_map, unit_map, context_toplevel, context_connector)
    
    return jsonld_output

def main():
    st.image(image_url)
    
    uploaded_file = st.file_uploader("Upload your metadata Excel file here", type=['xlsx'])
    
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
    st.image('https://drive.switch.ch/index.php/apps/files_sharing/ajax/publicpreview.php?x=2888&y=920&a=true&file=Funders.PNG&t=lgmDOqzgpyFi5Gh&scalingup=0', width=700)



if __name__ == "__main__":
    main()
