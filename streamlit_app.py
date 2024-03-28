import streamlit as st
import pandas as pd
import json
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
To use our Excel to JSON-LD converter, fill out the [metadata Excel file](https://drive.switch.ch/index.php/s/FUDeeav6Adf06iU) in the specified value column.
It is perfectly acceptable if not all rows are filled in; leaving some rows empty does not affect the script's operation.
Simply upload the filled Excel metadata file and our BattINFO converter will convert it into JSON-LD file.

# Acknowledgement 
BattINFO converter web application was developed at Empa, Swiss Federal Laboratories for Materials Science and Technology, Material for Energy Conversion lab.


This work has been developed under the following project and funding agencies: 
- [PREMISE](https://github.com/ord-premise)  
  
- [Battery 2030+](https://battery2030.eu/)  


"""

image_url = 'https://drive.switch.ch/index.php/apps/files_sharing/ajax/publicpreview.php?x=2888&y=920&a=true&file=BattINFO%2520converter%2520logo.PNG&t=bxd8AZRM6CDTFeM&scalingup=0'


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
    st.image(image_url)
    
    uploaded_file = st.file_uploader("Upload your metadata Excel file here", type=['xlsx'])
    
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
    
    st.markdown(markdown_content, unsafe_allow_html=True)
    st.image('https://drive.switch.ch/index.php/apps/files_sharing/ajax/publicpreview.php?x=2888&y=920&a=true&file=Funders.PNG&t=lgmDOqzgpyFi5Gh&scalingup=0', width=700)



if __name__ == "__main__":
    main()
