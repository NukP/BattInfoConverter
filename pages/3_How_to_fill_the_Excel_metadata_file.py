import streamlit as st

markdown_content = """
## How to Fill Out the Excel Metadata File

- All the tabs present in the Excel file are essential for the web app. **Do not change their names**.
- The first row of each tab contains the column names. These are also used by the web app. **Do not change their names**.
- To fill in the metadata using our template file, simply fill in the data in the `JSON - Info` tab and `Schema` tab.

### JSON - Info Tab
This tab contains the information that is displayed at the top level of the JSON-LD file. The logic of representing this information is slightly different from the one in the `Schema` tab. Hence, they are placed in a different tab. Simply fill in the value in the `Key` column.

### Schema Tab
This tab contains the majority of the metadata file.
- **Value**: Enter the metadata value. If the cell is empty, the script will skip this metadata item.  
- **Unit**: Specify the unit of the metadata. If the metadata item doesn't require a unit, enter "No Unit". Leaving this cell empty will cause an error.  
- **Ontology Link**: Provide the ontology link. If you do not want to ontologize a particular row, enter "NotOntologize". To add a comment instead, enter "Comment".

"""
#####################################################################

st.markdown(markdown_content, unsafe_allow_html=True)


