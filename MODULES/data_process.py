import tkinter as tk
from tkinter import Entry
# from tkinter import filedialog
from tkinter import messagebox
import sqlite3
import re
from datetime import datetime
from MODULES.vars import varsco
from MODULES.sql_name_validate import name_validate_sql

def process_file_after_save(file_path, t_name, sheet_name, all_tabs, sufijo, f_columns): #name_path_file, table_name.get(), list_sheets.get(),var.get()
    # Abre el diálogo para seleccionar una carpeta
    # carpeta = filedialog.askdirectory(title="Selecciona una carpeta")

    # if carpeta:
    
    if all_tabs:
        #LISTA DE HOJAS VALIDADAS
        # SHEET_OK_INSERT = []
        # if extension_user == '.xls':
        table_error_name = []
        column_name_error = []
        if varsco["extension_user"] == '.xlsx':
            hojas = varsco["workbook"].sheetnames
        elif varsco["extension_user"] == '.xls':
            hojas = ["workbook"].sheet_names()
        else:
            raise ValueError("Formato de archivo no soportado: usa .xls o .xlsx")

        for hoja in hojas:
            sheet_table_name = hoja.lower()
            validate_name = name_validate_sql(sheet_table_name)
            if validate_name[0]:
                print("Tabla lista para ser insertada",sheet_table_name)
                #SELECCIONA LA HOJA ACTUAL EN ITERACION Y OBTIENE LA CABECERA O PRIMERA FILA
                if varsco["extension_user"] == '.xlsx':
                    sheet = varsco["workbook"][hoja]
                    # Leer la primera fila (títulos)
                    #row_title = [cell.value for cell in sheet[1]]
                    row_title = [cell.value for cell in sheet[1] if cell.value and str(cell.value).strip() != ""]
                elif varsco["extension_user"] == '.xls':
                    hojas = varsco["workbook"].sheet_by_name(hoja)
                    #row_title = hojas.row_values(0)
                    row_title = [value for value in hojas.row_values(0) if value and str(value).strip() != ""]
                else:
                    raise ValueError("Formato de archivo no soportado: usa .xls o .xlsx")
                
                print(f"Columnas de la hoja {hoja}",row_title)
                # VALIDA TODAS LAS COLUMAS PARA CADA HOJA
                all_columns_validate_pivot = True
                for column in row_title:
                    sheet_column_name = column.lower()
                    validate_name_column = name_validate_sql(sheet_column_name)
                    if validate_name_column[0]:
                        print(f"     >>> Column OK -> {column}")
                    else:
                        all_columns_validate_pivot = False
                        #AGREGA EL ERROR DE LA VALIDADCION DE NOMBRES PARA LA COLUMNA DE CADA HOJA
                        column_name_error.append(f"SHEET [ {hoja} ]: {validate_name_column[1]}")
                #SOLO SI TODAS LAS COLUMNAS DE LA HOJA PASARON EL CONTROL SE AGREGA A LA LISTA DE HOJAS A PROCESAR
                if all_columns_validate_pivot:
                    varsco["SHEET_OK_INSERT"].append(hoja)
            else:
                #AGREGA EL MENSAJE DE ERROR DE LA VALIDACION DE NOMBRE PARA LA HOJA
                table_error_name.append(validate_name[1])
        
        #Muestra mensaje de alerta con las tablas con las que se tuvo problemas
        message_error= ""
        if len(table_error_name):
            message_error = "NOMBRES DE HOJAS\n"
            for i in table_error_name:
                message_error = message_error+f"\n - {i}"

        if len(column_name_error):
            message_error = message_error+"\nNOMBRES DE COLUMNAS\n"
            for i in column_name_error:
                message_error = message_error+f"\n - {i}"
        if len(column_name_error) or len(table_error_name): 
            
            if messagebox.askyesno("ALERTA - Hojas no aptas", f"{message_error}\nLas hojas mencionadas no se tomaran en cuenta\n¿Desea continuar?"):
                varsco["insert_data"].set(True)
            else:
                messagebox.showinfo("RECOMENDACIÓN", "Corrige las alertas mostradas y vuelve a intentarlo")
        else:
            varsco["insert_data"].set(True)
            # SQL_INSERT_DATA(SHEET_OK_INSERT,[])
    else:

        column_name_error = []
        if len(sheet_name)>0 and len(t_name)>0:
            print("Tabla lista para ser insertada",t_name)
            #SELECCIONA LA HOJA ACTUAL EN ITERACION Y OBTIENE LA CABECERA O PRIMERA FILA

            if varsco["extension_user"] == '.xlsx':
                sheet = varsco["workbook"][sheet_name]
                # Leer la primera fila (títulos)
                #row_title = [cell.value for cell in sheet[1]]
                row_title = [cell.value for cell in sheet[1] if cell.value and str(cell.value).strip() != ""]
            elif varsco["extension_user"] == '.xls':
                hojas = varsco["workbook"].sheet_by_name(sheet_name)
                #row_title = hojas.row_values(0)
                row_title = [value for value in hojas.row_values(0) if value and str(value).strip() != ""]
            else:
                raise ValueError("Formato de archivo no soportado: usa .xls o .xlsx")
            print(f"Columnas de la hoja {sheet_name}",row_title)
            # VALIDA TODAS LAS COLUMAS PARA CADA HOJA
            all_columns_validate_pivot = True

            #EXTRAE DATOS DE LAS ENTRADAS DE TEXTO
            for widget in f_columns.winfo_children():
                if isinstance(widget, Entry):
                    # print("HOLA",widget.get())
                    sheet_column_name = widget.get().lower()
                    validate_name_column = name_validate_sql(sheet_column_name)
                    if validate_name_column[0]:
                        print(f"     >>> Column OK -> {sheet_column_name}")
                    else:
                        all_columns_validate_pivot = False
                        #AGREGA EL ERROR DE LA VALIDADCION DE NOMBRES PARA LA COLUMNA DE CADA HOJA
                        column_name_error.append(f"SHEET [ {sheet_name} ]: {validate_name_column[1]}")
            if all_columns_validate_pivot:
                print("Listo para insertar")
                varsco["insert_data_one"].set(True)
                # SQL_INSERT_DATA(
                #     [sheet_name], #PESTAÑAS DEL EXCEL
                #     [t_name] # NOMBRE PERSONALIZADO DE LA TABLA
                # )
            else:
                message_error = ""
                if len(column_name_error):
                    message_error = message_error+"\nNOMBRES DE COLUMNAS\n"
                    for i in column_name_error:
                        message_error = message_error+f"\n - {i}"
                        
                    messagebox.showinfo("ALERTA", f"{message_error}\n Los nombres de columnas anteriores deben ser corregidos" )
        else:
                if len(sheet_name) == 0:
                    messagebox.showwarning("Alerta", "Debe seleccionar una Hoja")
                elif len(t_name) == 0:
                    messagebox.showwarning("Alerta", "Debe asignar un nombre como tabla")