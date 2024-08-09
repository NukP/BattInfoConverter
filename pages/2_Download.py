import streamlit as st

markdown_content = """

<p style="color:red; font-size:20px;">This is not the latest file for the version 0.6.0. 
Please refer to the latest file in the email. I will upload the final version of the Excel file once it has been finalized with Corsin and Simon.</p>

## Excel metadata files
Here you will find an Excel file template that you can fill out with your metadata
We will add more template for other cell types in the future. Be sure to check out!
### Blank Excel metadata file
[Coin cell battery schema version 0.1.0](https://raw.githubusercontent.com/NukP/xls_convert/fix_oslo2/Excel%20for%20reference/CoinCellBattery_Schemas_version_010.xlsx) 
### Example filled out Excel metadata file
[Example-filled Coin cell battery schema version 0.1.0](https://raw.githubusercontent.com/NukP/xls_convert/fix_oslo2/Excel%20for%20reference/Example_CoinCellBattery_Schemas_version_010.xlsx)


"""
#####################################################################

st.markdown(markdown_content, unsafe_allow_html=True)


