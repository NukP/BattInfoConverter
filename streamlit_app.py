import streamlit as st
import pandas as pd
import json
from io import BytesIO

markdown_content = """
# Excel to JSON-LD converter
Ontologizing your metadata can significantly enhance the interoperability of data across various research groups. To learn more about ontologizing your metadata, we invite you to visit our page on [ontologizing metadata](https://github.com/ord-premise/interoperability-guidelines/tree/main). While the benefits of this process are clear, it can often be a daunting task in practice. With this in mind, we've developed an Excel to JSON-LD web application designed to streamline and expedite this intricate task, making it more manageable for you and your team.

# Usage
To use our Excel to JSON-LD converter, fill out the metadata Excel file (Battery_schemas.xlsx) in the specified value column. It is perfectly acceptable if not all rows are filled in; leaving some rows empty does not affect the script's operation. Then, launch our [Excel to JSON-LD app](https://testxlsconv.streamlit.app/) and upload the completed metadata Excel file. Our application will efficiently convert your metadata into a JSON-LD file.

# Authors
[Nukorn Plainpan](https://github.com/NukP)  
Postdoctoral researcher

Corsin Battaglia  
principal investigator

# Acknowledgement 
This Excel metadata for coin cell battery file and Excel to JSON-LD converter web application was developed at Material for Energy Conversion lab, Swiss Federal Laboratories for Materials Science and Technology (Empa). 

This work has been developed under the following project: 
- [PREMISE](https://github.com/ord-premise)  
  ![image](https://github.com/ord-premise/metadata-batteries/assets/45081142/74640b5c-ee94-41e1-9acd-fa47da866fe8)
  
- [Battery 2030+](https://battery2030.eu/)  
<img src="https://battery2030.eu/wp-content/uploads/2021/08/battery2030-logo-white-text-B.png" width="300">
"""


def create_jsonld_with_conditions(schemas, item_id_map, connector_id_map):
    jsonld = {
        "@context": {
            "@vocab": "http://emmo.info/electrochemistry#",
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        },
        "@graph": []
    }

    top_level_items = {}

    for _, row in schemas.iterrows():
        if pd.isna(row['Value']) or row['Ontology link'] == 'NotOntologize':
            continue  # Skip rows with empty value or 'NotOntologize' in Ontology link

        ontology_links = row['Ontology link'].split('-')
        if len(ontology_links) < 5:
            continue  # Skip rows with insufficient parts in Ontology link

        value = row['Value']
        unit = row['Unit']

        main_item = ontology_links[0]
        relation = ontology_links[1]
        sub_item = ontology_links[2]
        property_relation = ontology_links[3]
        property_item = ontology_links[4]

        if main_item not in top_level_items:
            top_level_items[main_item] = {
                "@type": main_item,
                relation: []
            }
            jsonld["@graph"].append(top_level_items[main_item])

        sub_item_structure = {
            "@type": sub_item,
            property_relation: [{
                "@type": property_item,
                "hasValue": value,
                "hasUnits": unit
            }]
        }

        jsonld["@context"].update({
            main_item: {"@id": item_id_map.get(main_item, ""), "@type": "@id"},
            sub_item: {"@id": item_id_map.get(sub_item, ""), "@type": "@id"},
            property_item: {"@id": item_id_map.get(property_item, ""), "@type": "@id"}
        })

        top_level_items[main_item][relation].append(sub_item_structure)

    return jsonld

def convert_excel_to_jsonld(excel_file):
    # Assuming the Excel file has the necessary sheets named 'Schemas', 'Ontology - item', 'Ontology - Connector'
    excel_data = pd.ExcelFile(excel_file)
    
    schemas = pd.read_excel(excel_data, sheet_name='Schemas')
    item_id_map = pd.read_excel(excel_data, sheet_name='Ontology - item').set_index('Item')['ID'].to_dict()
    connector_id_map = pd.read_excel(excel_data, sheet_name='Ontology - Connector').set_index('Item')['ID'].to_dict()

    jsonld_output = create_jsonld_with_conditions(schemas, item_id_map, connector_id_map)
    
    return jsonld_output

def main():
    st.markdown(markdown_content, unsafe_allow_html=True)
    st.title("Excel to JSON-LD Converter")
    
    uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx'])
    
    if uploaded_file is not None:
        # Convert the uploaded Excel file to JSON-LD
        jsonld_output = convert_excel_to_jsonld(uploaded_file)
        
        # Convert JSON-LD output to a string to display in text area (for preview)
        jsonld_str = json.dumps(jsonld_output, indent=4)
        st.text_area("JSON-LD Output", jsonld_str, height=3000)
        
        # Convert JSON-LD output to a downloadable file
        to_download = BytesIO(jsonld_str.encode())
        st.download_button(label="Download JSON-LD",
                           data=to_download,
                           file_name="converted.jsonld",
                           mime="application/json")

if __name__ == "__main__":
    main()
