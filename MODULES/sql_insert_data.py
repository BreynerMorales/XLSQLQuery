import re
import sqlite3
from tkinter import messagebox
from datetime import datetime
# from tkinter import filedialog
from MODULES.vars import varsco
def SQL_INSERT_DATA(list_sheet_names_ok,name_from_edittable,sufijo=""): #name_from_edittable existe una lista con un unico elemento cuando el usuario elige solo una pestaña del libro excel
    
    sufijo_table = sufijo.replace(" ","")
    if len(sufijo_table):
        if not re.match("^[a-zA-Z0-9_]+$", sufijo_table):
            return messagebox.showinfo("Alerta", f"El sufijo [{sufijo_table}] solo debe contener letras, números y guiones bajos, elimina los demas caracteres")
        
    print("HOJAS VALIDADAS",list_sheet_names_ok)
    # Conectar a la base de datos (si no existe, se crea)
    # conexion = sqlite3.connect(f'{carpeta}/data_main.db')
    conexion = sqlite3.connect(varsco["path_database"])
    cursor = conexion.cursor()
    for sheet_item in list_sheet_names_ok:
        
        sheet_browser = sheet_item
        
        #Cambia el nombre personalizado de la tabla si existe
        if len(name_from_edittable):
            sheet_item = name_from_edittable[0]
        
        sheet_item = f"{sheet_item.lower()}{sufijo_table}"

        print("Crear tabla:", sheet_item)
        # Consulta para verificar existencia
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (sheet_item,))
        existe = cursor.fetchone() is not None
        
        if existe:
            print(f"La tabla '{sheet_item}' existe.")
            # conexion.close()
            messagebox.showwarning("Alerta", f'La tabla "{sheet_item}" será omitida porque ya existe')
        else:
            try:
                if varsco["extension_user"] == '.xlsx':
                    sheet_now = varsco["workbook"][sheet_browser]
                    # Leer la primera fila (títulos)
                    #row_title_sheet = [cell.value for cell in sheet_now[1]]
                    row_title_sheet = [cell.value for cell in sheet_now[1] if cell.value and str(cell.value).strip() != ""]
                    nrows = sheet_now.max_row
                    if not(nrows > 1): 
                        raise ValueError(f"La Hoja '{sheet_browser}' esta vacia")
                    else:
                        lista_muestra = [cell.value for cell in sheet_now[2]]
                        row_muestra_sheet = lista_muestra[:len(row_title_sheet)]

                elif varsco["extension_user"] == '.xls':
                    sheet_now = varsco["workbook"].sheet_by_name(sheet_browser)
                    row_title_sheet = sheet_now.row_values(0)
                    nrows = sheet_now.nrows
                    if not(nrows > 1): 
                        # print(f"La Hoja {sheet_browser} esta vacia")
                        raise ValueError(f"La Hoja '{sheet_browser}' esta vacia")
                    else:
                        lista_muestra = sheet_now.row_values(1)
                        row_muestra_sheet = lista_muestra[:len(row_title_sheet)]
                else:
                    raise ValueError("Formato de archivo no soportado: usa .xls o .xlsx")
                
                
                # row_muestra_sheet = sheet_now.row_values(1)
                # Trabaja con la fila aquí
                estructura_sql = ''
                estructura_sql_columns = ''
                estructura_sql_columns_signo = ''
                
                #EXTRAE DATOS DE LAS ENTRADAS DE TEXTO
                column_muestra = 0
                print(sheet_item,row_muestra_sheet)
                for col in row_muestra_sheet:
                    data_column = row_muestra_sheet[column_muestra]
                    data_type = None
                    if  data_column == None or type(data_column) == str or isinstance(data_column, datetime):
                        data_type = "TEXT"
                    elif  type(data_column) == int or type(data_column) == float:
                        data_type = "REAL"
                    
                    estructura_sql+= f"{row_title_sheet[column_muestra]} {data_type}"
                    estructura_sql_columns+= f"{row_title_sheet[column_muestra]}"
                    estructura_sql_columns_signo+= "?"
                    if column_muestra+1 < len(row_title_sheet):
                        estructura_sql+=", "
                        estructura_sql_columns+=", "
                        estructura_sql_columns_signo+=", "
                    print("Column: ", row_title_sheet[column_muestra],col, data_type)
                    column_muestra+=1
                # Crear la tabla
                print(f"CREATE TABLE IF NOT EXISTS {sheet_item} ({estructura_sql})")
                cursor.execute(f'''CREATE TABLE IF NOT EXISTS {sheet_item} ({estructura_sql})''')
                conexion.commit()
                
                #==================================================================
                # INSERTAR LOS REGISTROS EN LA NUEVA TABLA
                #==================================================================
                first_sheet = sheet_now
                
                
                data_insert = []


                if varsco["extension_user"] == '.xlsx':
                    # Iterar desde la segunda fila (saltando encabezados)
                    for row in first_sheet.iter_rows(min_row=2, values_only=True):
                        data_insert.append(list(row[:len(row_title_sheet)]))
                elif varsco["extension_user"] == '.xls':
                    for row_idx in range(1, first_sheet.nrows):  # Salta la fila de encabezados
                        fila = first_sheet.row_values(row_idx)
                        data_insert.append(fila)
                else:
                    raise ValueError("Formato de archivo no soportado: usa .xls o .xlsx")
                
                print(f"INSERT INTO {sheet_item} ({estructura_sql_columns}) VALUES ({estructura_sql_columns_signo})")
                cursor.executemany(f"INSERT INTO {sheet_item} ({estructura_sql_columns}) VALUES ({estructura_sql_columns_signo})", data_insert)
                conexion.commit()
            except ValueError  as e:
                print(e)
                messagebox.showinfo("Alerta", e)

    conexion.close()
    # Muestra la notificación
    print(r"""
 _____        _        _                              
|  __ \      | |      | |                             
| |  | | __ _| |_ __ _| |__   __ _ ___  ___  
| |  | |/ _` | __/ _` | '_ \ / _` / __|/ _ \_
| |__| | (_| | || (_| | |_) | (_| \__ \  __/
|_____/ \__,_|\__\__,_|_.__/ \__,_|___/\___|    

(  )   ___ 
 ||  / __|
 ||  \__ \_
 ||  |___/
                                                  
 _____  ______   ____   ____   __     __  
|  __ \|  ____| | __ \ |  _  \ \ \   / /         
| |__) | |__   | |__\ || | \ |  \ \_/ /                 
|  _  /|  __|  |  __  || | | |   \   /                  
| | \ \| |____ | |  | || |_| |  |  |                   
|_|  \_\______|| |  | |\____/  |__|                   

                D A T A B A S E   R E A D Y
                            Powered  by Breyner J.
""")