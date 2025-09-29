# Diccionario de variables y constantes
# from tkinter import *
import tkinter as tk

varsco = {
    # Variable para almacenar el estado del Checkbutton
    # "var": False,
    # "var_saved": False,
    "var": None,
    "var_saved": None,
    # "var": tk.BooleanVar(value=False),
    # "var_saved": tk.BooleanVar(value=False),
    "name_path_file" : '',
    "path_database":"DATA/data_main.db",
    "row_muestra" : None,
    "row_title" : None,
    "workbook" : None,
    "extension_user" : None,
    "URL_DATABASE" : None,
    "DATA_EXECUTE" : None,
    "insert_data":None,
    "insert_data_one":None,
    "SHEET_OK_INSERT":[],
    
    "RESERVED_WORDS": [
                        "with","select", "insert", "update", "delete", "from", "where", "join", "into", "drop", "alter", "create",
                        "table", "column", "values", "as", "and", "or", "not", "is", "in", "like", "between", "group", "having",
                        "order", "by", "distinct", "union", "left", "right", "inner", "outer", "exists", "case", "when", "then",
                        "else", "end", "null", "true", "false", "on", "between", "like", "limit", "offset", "primary", "foreign",
                        "key", "check", "constraint","count","IF","TEMP",";",",","=","DATE","DATE","DATETIME","hours","day","now"
                    ]
}