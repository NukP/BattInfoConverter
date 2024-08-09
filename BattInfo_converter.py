"""
This module handle the interface of the web app. 
"""
import streamlit as st
import json
import os
from io import BytesIO
import json_convert as js_conv 


markdown_content = """ 
Ontologizing your metadata can significantly enhance the interoperability of data across various research groups.
To learn more about ontologizing your metadata, we invite you to visit our page on
[ontologizing metadata](https://github.com/ord-premise/interoperability-guidelines/tree/main). 
While the benefits of this process are clear, it can often be a daunting task in practice. 
With this in mind, we've developed an BattINFO converter web application designed to streamline and expedite this intricate task,
making it more manageable for you and your team.

BattINFO converter helps you ontologize metadata for coin cell battery based on [BattINFO](https://big-map.github.io/BattINFO/index.html) ontology. 

__For additional information and example Excel metadata files, please click the respective link on the left__

# Acknowledgement 
BattINFO converter web application was developed at [Empa](https://www.empa.ch/), Swiss Federal Laboratories for Materials Science and Technology in [Material for Energy Conversion lab](https://www.empa.ch/web/s501).  


We acknowledge stimulating discussions and support from Dr Simon Clark, SINTEF, Norway.


This work has been developed under the following project and funding agencies: 
- [PREMISE](https://ord-premise.org/)  
  
- [Battery 2030+](https://battery2030.eu/)

- [Big-Map project](https://www.big-map.eu/)


"""

image_url = 'https://raw.githubusercontent.com/NukP/xls_convert/fix_oslo2/BattInfoCOnverter.png'

def main():
    st.image(image_url)
    
    st.markdown(f"__App Version: {js_conv.APP_VERSION}__")
    
    uploaded_file = st.file_uploader("__Upload your metadata Excel file here__", type=['xlsx', 'xlsm'])
    
    if uploaded_file is not None:
        # Extract the base name of the file (without the extension)
        base_name = os.path.splitext(uploaded_file.name)[0]
        
        # Convert the uploaded Excel file to JSON-LD
        jsonld_output = js_conv.convert_excel_to_jsonld(uploaded_file)
        jsonld_str = json.dumps(jsonld_output, indent=4)

        # Download button
        to_download = BytesIO(jsonld_str.encode())
        output_file_name = f"BattINFO_converter_{base_name}.json"  
        st.download_button(label="Download JSON-LD",
                        data=to_download,
                        file_name=output_file_name,
                        mime="application/json")
        
        # Convert JSON-LD output to a string to display in text area (for preview)
        st.text_area("JSON-LD Output", jsonld_str, height=1000)
    
    st.markdown(markdown_content, unsafe_allow_html=True)
    st.image('https://raw.githubusercontent.com/NukP/xls_convert/fix_oslo2/sponsor.png', width=700)

if __name__ == "__main__":
    main()

