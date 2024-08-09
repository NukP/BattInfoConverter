import streamlit as st

markdown_content = """
## How to adapt the Excel metadata file for your own custom data
1. **Adding New Ontology Terms**:
    - Go to the website providing the ontology concept (e.g., BattInfo, Schema.org).
    - In the `@context-TopLevel` tab, add the top-level URL of the ontology website.
    - In the `Ontology - Item` tab, define the new ontology term. Use the `Item` column for the term and the `Key` column for the ontology reference (e.g., `schemas:identifier`).

2. **Adding New Units**:
    - In the `Ontology - Unit` tab, define the new unit. Include the `Item`, `Label`, and `Symbol` columns, along with the ontology reference in the `Key` column.

3. **Adding New Rows**:  
    - Add new rows to the `Schema` tab (or remove existing rows) to include additional metadata items. Ensure that the `Ontology link` column references the new ontology terms and units.

"""
#####################################################################

st.markdown(markdown_content, unsafe_allow_html=True)


