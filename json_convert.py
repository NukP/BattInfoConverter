from dataclasses import dataclass, field
import pandas as pd
import streamlit as st
import auxiliary as aux 
import datetime
from pandas import DataFrame
import numpy as np

APP_VERSION = "0.6.0"

@dataclass
class ExcelContainer:
    excel_file: str
    data: dict = field(init=False)

    def __post_init__(self):
        excel_data = pd.ExcelFile(self.excel_file)
        self.data = {
            "schema": pd.read_excel(excel_data, 'Schema'),
            "unit_map": pd.read_excel(excel_data, 'Ontology - Unit'),
            "context_toplevel": pd.read_excel(excel_data, '@context-TopLevel'),
            "context_connector": pd.read_excel(excel_data, '@context-Connector'),
            "info": pd.read_excel(excel_data, 'JSON - Info'),
            "unique_id": pd.read_excel(excel_data, 'Unique ID')
        }

def get_information_value(df: DataFrame, row_to_look: str, col_to_look: str = "Value", col_to_match: str = "Metadata") -> str | None:
    """
    Retrieves the value from a specified column where a different column matches a given value.

    Parameters:
    df (DataFrame): The DataFrame to search within.
    row_to_look (str): The value to match within the column specified by col_to_match.
    col_to_look (str): The name of the column from which to retrieve the value. Default is "Key".
    col_to_match (str): The name of the column to search for row_to_look. Default is "Item".

    Returns:
    str | None: The value from the column col_to_look if a match is found; otherwise, None.
    """
    result = df.query(f"{col_to_match} == @row_to_look")[col_to_look]
    return result.iloc[0] if not result.empty else None


def create_jsonld_with_conditions(data_container: ExcelContainer):
    schema = data_container.data['schema']
    context_toplevel = data_container.data['context_toplevel']
    context_connector = data_container.data['context_connector']

    #Harvest the information for the required section of the schemas
    ls_info_to_harvest = [
    "Cell type",
    "Cell ID",
    "Date of cell assembly",
    "Institution/company",
    "Scientist/technician/operator"
    ]

    ls_harvested_info = {}

    for field in ls_info_to_harvest:
        if not get_information_value(df=schema, row_to_look=field) is np.nan:
            raise ValueError(f"Missing information in the schema, please fill in the field '{field}'")
        else:
            ls_harvested_info[field] = get_information_value(df=schema, row_to_look=field)

    jsonld = {
        "@context": ["https://w3id.org/emmo/domain/battery/context", {}],
        "@type": ls_harvested_info['Cell type'],
        "schema:version": get_information_value(df=schema, row_to_look='BattINFO CoinCellSchema version'),
        # "schemas:productID": get_information_value(df=info, row_to_look='Cell ID'),
        # "schemas:dateCreated": str(get_information_value(df=info, row_to_look='Date of cell assembly')),
        "rdfs:comment": {}
    }

    for _, row in context_toplevel.iterrows():
        jsonld["@context"][1][row['Item']] = row['Key']

    connectors = set(context_connector['Item'])

    for _, row in schema.iterrows():
        if pd.isna(row['Value']) or row['Ontology link'] == 'NotOntologize':
            continue
        if row['Ontology link'] == 'Comment':
            jsonld["rdfs:comment"][row['Metadata']] = row['Value']
            continue
        if pd.isna(row['Unit']):
            raise ValueError(f"The value '{row['Value']}' is filled in the wrong row, please check the schema")

        ontology_path = row['Ontology link'].split('-')
        aux.add_to_structure(jsonld, ontology_path, row['Value'], row['Unit'], data_container)
    jsonld["rdfs:comment"]["BattINFO Converter version"] = APP_VERSION
    jsonld["rdfs:comment"]["Software credit"] = f"This JSON-LD was created using Battconverter (https://battinfoconverter.streamlit.app/) version: {APP_VERSION} and the schema version: {jsonld['schema:version']}, this web application was developed at Empa, Swiss Federal Laboratories for Materials Science and Technology in the Laboratory Materials for Energy Conversion lab"

    return jsonld

def convert_excel_to_jsonld(excel_file: ExcelContainer):
    print('*********************************************************')
    print(f"Initialize new session of Excel file conversion, started at {datetime.datetime.now()}")
    print('*********************************************************')
    data_container = ExcelContainer(excel_file)

    # Generate JSON-LD using the data container
    jsonld_output = create_jsonld_with_conditions(data_container)
    

    return jsonld_output