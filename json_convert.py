from dataclasses import dataclass, field
import pandas as pd
import streamlit as st
import auxiliary as aux 
import datetime

APP_VERSION = "0.4.0"

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

def get_information_value(df, col_to_look, row_to_look, col_to_match):
    """
    Return the value of a column "col_to_look" at the row where the column "col_to_match" is equal to row_to_look.
    If no match is found, return None.
    """
    result = df.query(f"{col_to_match} == @row_to_look")[col_to_look]
    return result.iloc[0] if not result.empty else None


def create_jsonld_with_conditions(data_container: ExcelContainer):
    schema = data_container.data['schema']
    info = data_container.data['info']
    context_toplevel = data_container.data['context_toplevel']
    context_connector = data_container.data['context_connector']

    jsonld = {
        "@context": ["https://w3id.org/emmo/domain/battery/context", {}],
        "@type": get_information_value(df=info, col_to_look='Key', row_to_look='Cell type', col_to_match='Item'),
        "schema:version": get_information_value(df=info, col_to_look='Key', row_to_look='BattINFO CoinCellSchema version', col_to_match='Item'),
        "schemas:productID": get_information_value(df=info, col_to_look='Key', row_to_look='Cell ID', col_to_match='Item'),
        "schemas:dateCreated": str(get_information_value(df=info, col_to_look='Key', row_to_look='Date of cell assembly', col_to_match='Item')),
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
    jsonld["rdfs:comment"]["Software credit"] = f"This JSON-LD was created using Battconverter (https://battinfoconverter.streamlit.app/) version: {APP_VERSION} and the schema version: {jsonld['schema:version']}, this web application was developed at Empa, Swiss Federal Laboratories for Materials Science and Technology in Material for Energy Conversion lab"

    return jsonld

def convert_excel_to_jsonld(excel_file):
    #print('Converting new Excel file')
    #print('\n')
    # Create an instance of ExcelContainer
    print('*********************************************************')
    print(f"Initialize new session of Excel file conversion, started at {datetime.datetime.now()}")
    print('*********************************************************')
    data_container = ExcelContainer(excel_file)

    # Generate JSON-LD using the data container
    jsonld_output = create_jsonld_with_conditions(data_container)
    

    return jsonld_output