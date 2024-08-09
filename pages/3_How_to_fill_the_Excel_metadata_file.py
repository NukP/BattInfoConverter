import streamlit as st

markdown_content = """
## How to Fill Out the Excel metadata file

1. All the tabs present in the Excel files are essential for the web app. __Do not change their names__.  
2. **First Row**: Ensure that the first row of each tab contains the column names. These names are used as references by the app.  
3. **Filling Data**: In the `Schema` tab, fill in the following columns:  
    - **Value**: Enter the metadata value. If the cell is empty, the script will skip this metadata item.  
    - **Unit**: Specify the unit of the metadata. If the metadata item doesn't require a unit, enter "No Unit". Leaving this cell empty will cause an error.  
    - **Ontology link**: Provide the ontology link. If you do not want to ontologize a particular row, enter "NotOntologize". To add a comment instead, enter "Comment".  



"""
#####################################################################

st.markdown(markdown_content, unsafe_allow_html=True)


