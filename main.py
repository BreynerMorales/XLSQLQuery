from tkinter import *
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import sqlite3

from tkinter import ttk
import re

# from tkinter import messagebox
import os

from MODULES.sql_name_validate import name_validate_sql
from MODULES.data_process import process_file_after_save
from MODULES.vars import varsco
from MODULES.open_file import open_file_excel
from MODULES.sql_insert_data import SQL_INSERT_DATA
from MODULES.execute import execute_query
class MiAplicacion(Tk):
    CONFIG = {
        "APP_TITLE": "SQLXEL Administrator v1.0.0 Powered by Breyner J",
        "APP_SIZE": "600x400",
        "APP_PATH_ICON": "SOURCE/icon.ico",
        "BACKGROUND_COLOR": "white",
        "BACKGROUND_COLOR1": "white",
        "FOREGROUND_COLOR": "black",
        "FOREGROUND_COLOR2": "black",
        "WARNING_COLOR": "orange",
        "ERROR_COLOR": "red",
        "ITEMS_NUMBER_EDITOR": "green"
    }

    def __init__(self):
        super().__init__()
        # Ahora ya existe la ventana root
        varsco["var"] = BooleanVar(value=False, master=self)
        varsco["var_saved"] = BooleanVar(value=False, master=self)
        varsco["insert_data"] = BooleanVar(value=False, master=self)
        varsco["insert_data_one"] = BooleanVar(value=False, master=self)

        # Configuración de la ventana principal
        self.title(self.CONFIG["APP_TITLE"])
        # self.geometry(self.CONFIG["APP_SIZE"])
        self.configure(bg=self.CONFIG["BACKGROUND_COLOR"])

        try:
            self.iconbitmap(self.CONFIG["APP_PATH_ICON"])
        except Exception as e:
            print(f"No se pudo cargar el ícono: {e}")

        Label(self, text="SQLXEL Administrator", font=("Arial", 12, "bold")).pack(fill=X)

        # Construcción de la interfaz
        self._crear_widgets()

    def _crear_widgets(self):
        """Crea y organiza los elementos gráficos (widgets)"""
        F_main = Frame(self, bg="green")
        F_main.pack(fill=BOTH)

        F_filter = LabelFrame(F_main, text="Filter and selection")
        F_filter.pack(fill=BOTH, expand=True,side=LEFT)
        Label(F_filter,text="Origin").pack(expand=True, fill=X)
        self.lbl_file_path = Entry(F_filter)
        self.lbl_file_path.pack(expand=True, fill=X)
        Label(F_filter,text="Destination").pack(expand=True, fill=X)
        self.lbl_file_path_out = Entry(F_filter)
        self.lbl_file_path_out.pack(expand=True, fill=X)

        FR_input = Frame(F_filter)
        FR_input.pack()

        Label(FR_input, text="Select sheet :").grid(        row=0, column=0, sticky='e')
        Label(FR_input, text="Name as table :").grid(       row=0, column=2, sticky='e')
        Label(FR_input, text="All of the sheets :").grid(   row=0, column=4, sticky='e')
        Label(FR_input, text="Suffix :").grid(              row=0, column=6, sticky='e')
        Label(FR_input, text="Save locally :").grid(        row=0, column=8, sticky='e')

        # === Canvas + Scrollbar en el contenedor principal ===
        wrapper = Frame(F_filter)
        wrapper.pack(fill="both", expand=True)

        self.canvas = Canvas(wrapper, height=120)
        self.canvas.pack(side="top", fill="both", expand=True)

        scroll_x = Scrollbar(wrapper, orient="horizontal", command=self.canvas.xview)
        scroll_x.pack(side="bottom", fill="x")
        self.canvas.configure(xscrollcommand=scroll_x.set)

        # === self.f_columns está completamente vacío y será usado como contenedor temporal ===
        self.f_columns = Frame(self.canvas)  # <<<<<< ESTE es el frame vacío
        self.canvas.create_window((0, 0), window=self.f_columns, anchor="n")
        self.f_columns.bind("<Configure>", self.actualizar_scroll)

        # Crear el Combobox
        self.list_sheets = ttk.Combobox(FR_input,state="readonly")
        self.list_sheets.grid(row=0, column=1, sticky='w')
        self.list_sheets.bind("<<ComboboxSelected>>", self.al_seleccionar_hoja)
        self.table_name = Entry(FR_input)
        self.table_name.grid(row=0, column=3, sticky='we')
        self.sufijo_name = Entry(FR_input)
        self.sufijo_name.grid(row=0, column=7, sticky='we')

        # Crear el Checkbutton
        self.checkbutton = Checkbutton(FR_input, text="No", variable=varsco["var"], command=self.cambiar_texto)
        self.checkbutton.grid(row=0, column=5, sticky='w')

        self.checkbutton_save = Checkbutton(FR_input, text="No", variable=varsco["var_saved"], command=self.cambiar_texto_save)
        self.checkbutton_save.grid(row=0, column=9, sticky='w')

        FR_BTN_main = Frame(FR_input)
        FR_BTN_main.grid(row=1, column=0, columnspan=9) 

        Button(FR_BTN_main, text="Open file", bg="green",fg="white",font=("arial",12,"bold"), command=lambda: self.get_file_path(self.lbl_file_path,self.list_sheets,self.f_columns)).grid(row=0, column=0)
        self.BTN_CHARGE_DATA=Button(FR_BTN_main, text="Data load",bg="lightgreen",fg="black",font=("arial",12,"bold"), command=lambda: self.save_data_met())
        self.BTN_CHARGE_DATA.grid(row=0, column=1)

        BTN_REFRESH=Button(FR_BTN_main, text="Refresh", bg="lightblue",fg="black",font=("arial",12,"bold"), command=lambda: self.refrescar())
        BTN_REFRESH.grid(row=0, column=2)

        F_database = LabelFrame(F_main,text="Database")
        F_database.pack(side=RIGHT,fill=BOTH)

        # Estilos para Treeview
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)  # Ajustar altura de filas


        # Crear un Treeview con columnas
        self.tree = ttk.Treeview(F_database, columns=("Table", "Columns"), show="headings", height=5)

        # Definir encabezados
        self.tree.heading("Table", text="Table")
        self.tree.heading("Columns", text="Columns")

        # Configurar ancho de columnas
        self.tree.column("Table", width=190, anchor="w")
        self.tree.column("Columns", width=100, anchor="center")

        # Definir colores con tags
        self.tree.tag_configure("padre", background="lightblue")   # Rojo claro
        self.tree.tag_configure("hijo", background="#ccffcc")    # Verde claro
        self.tree.tag_configure("especial", background="#ccccff")  # Azul claro

        self.get_database_info(self.tree)
        # Posicionar el Treeview
        self.tree.pack(expand=True, fill="both")

        frm_query = Frame(self, bg="red")
        frm_query.pack(fill=BOTH)

        F_editor = Frame(frm_query)
        F_editor.pack(fill=BOTH)

        self.item_numbers = Text(F_editor, height=15,width=4, wrap="none",bg='black',font=("Courier",11,"bold"),fg='green',insertbackground='white')  # wrap="word" evita cortar palabras
        self.item_numbers.pack(side=LEFT, fill=X)

        self.texto = Text(F_editor, height=15, bg='black',wrap="none",font=("Courier",11,"bold"),fg='white',insertbackground='white')  # wrap="word" evita cortar palabras
        self.texto.pack(side=LEFT, fill=X, expand=True)
        self.texto.focus_set()

        # Asociar la función al evento de escribir (KeyRelease)
        self.texto.bind("<KeyRelease>", self.marcar_palabras)
        #self.texto.bind("<Return>", line_enter)
        #self.texto.bind("<Delete>", line_delete)
        scrollbar = Scrollbar(F_editor)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Configurar los widgets Text para que usen el mismo Scrollbar
        self.item_numbers.config(yscrollcommand=scrollbar.set)
        self.texto.config(yscrollcommand=scrollbar.set)

        # Configurar el Scrollbar para que maneje el desplazamiento de ambos widgets
        scrollbar.config(command=lambda *args: [self.item_numbers.yview(*args),self.texto.yview(*args)])

        
        # Asociar el evento de rueda del ratón en ambos widgets
        self.texto.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.item_numbers.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.item_numbers.insert(END, "1")
        self.item_numbers.config(state="disabled")

        Button(self,text="Execute query",font=("Arial",12,"bold"), cursor="hand2",background="orange",fg="black",command=lambda:self.execute_query(self.texto.get("1.0", END))).pack()
        frm_response_iten = Frame(self,bg="grey")
        frm_response_iten.pack(fill=BOTH)
        # Crear un Treeview con columnas
        self.TREE_item = ttk.Treeview(frm_response_iten, columns=("item", "Query"), show="headings", height=3)

        # Definir encabezados
        self.TREE_item.heading("item", text="Item")
        self.TREE_item.heading("Query", text="Query")
        self.TREE_item.bind("<<TreeviewSelect>>", self.on_row_selected)
        self.TREE_item.pack(expand=True, fill="both")

        self.bind("<Configure>", self.on_resize)
        self.frm_response_show = Frame(self, bg="#f0f0f0")
        self.frm_response_show.pack(fill=BOTH, expand=True)
        print(r"""
                    _____   ____   __     __   __ ______ __      __ 
                    / ____  / __ \ | |     \ \ / /|  ____| |     | | This is a aplication 
                    | (____ | |  | || |      \ V / | |__  | |     | | desingned for convert 
                    \____  \| |  | || |       > <  |  __| | |     | | Excel files in tables 
                    ____) )| |__| || |____  / . \ | |____| |____ |_| of the database whit 
                    |_____/  \____/ |______|/_/ \_\|______|______|(_) powered by SQLite.
                                \_\_
                                    # Your App is ready #
                                                Developed by Breyner J.
        """)
    def execute_query(self,data_text):
        for item in self.TREE_item.get_children():
            self.TREE_item.delete(item)
        execute_query(data_text)
        line_query = 1
        for i in varsco["DATA_EXECUTE"]:
            # Definir estilos de fila alternos usando tags
            self.TREE_item.tag_configure('evenrow', background='#f0f0f0')  # gris claro
            self.TREE_item.tag_configure('oddrow', background='white')     # blanco
            self.TREE_item.tag_configure('error', background='#FF7659')     # blanco
            tag = 'evenrow' if line_query % 2 == 0 else 'oddrow'
            if i[1] == "Error":
                tag = 'error'
            self.TREE_item.insert("", "end", values=(line_query, f"{f'[{i[1]}] {i[2]} in {i[0]}' if i[1] == 'Error' else F'[OK] {i[0]}'}"),tags=(tag,)) #, tags=(tag,)
            line_query+=1


    def get_file_path(self,lbl_file_path,list_sheets,f_columns):
        #global name_path_file  # Declaración global para usar la variable fuera de la función
        file = filedialog.askopenfilename(
            title="Selecciona un archivo Excel",
            filetypes=[
                ("Archivos compatibles", "*.xls *.xlsx *.csv"),  # <- filtro combinado
                ("Archivos Excel (.xls)", "*.xls"),
                ("Archivos Excel (.xlsx)", "*.xlsx"),
                ("Archivos CSV", "*.csv"),
                ("Todos los archivos", "*.*")
            ]
        )

        if file:
            print(f"Archivo seleccionado: {file}")
            lbl_file_path.delete(0, tk.END)      # Borrar todo el contenido
            lbl_file_path.insert(0, file)  # Insertar texto desde el inicio
            varsco["name_path_file"] = file  # Asignación de la variable global
            open_file_excel(file,list_sheets,f_columns)
            self.BTN_CHARGE_DATA.config(state="normal")
    
    def save_data_met(self):
        if varsco["var_saved"].get(): 
            file_path = varsco["path_database"]
        else:
            file_path = filedialog.asksaveasfilename(
                title="Guardar base de datos SQLite como...",
                defaultextension=".db",  # Extensión por defecto si el usuario no pone una
                filetypes=[
                    ("SQLite Database (*.db, *.sqlite, *.sqlite3, *.db3, *.sdb, *.sl3)",
                    "*.sqlite *.sqlite3 *.db *.db3 *.sdb *.sl3"),
                    ("Todos los archivos", "*.*")
                ]
            )
        if not(file_path):
            messagebox.showwarning("Alerta", 'Debe seleccionar una ruta para almacenar la base de datos')
            return
        else:
            process_file_after_save(
                file_path,
                self.table_name.get(),
                self.list_sheets.get(),
                varsco["var"].get(),
                self.sufijo_name.get(),
                self.f_columns
            )

            insertar = False  # bandera para saber si refrescar y actualizar ruta

            if varsco["insert_data"].get():
                varsco["insert_data"].set(False)
                SQL_INSERT_DATA(varsco["SHEET_OK_INSERT"], [])
                insertar = True

            if varsco["insert_data_one"].get():
                varsco["insert_data_one"].set(False)
                SQL_INSERT_DATA(
                    [self.list_sheets.get()],     # Pestañas del Excel
                    [self.table_name.get()],      # Nombre personalizado de la tabla
                    self.sufijo_name.get()
                )
                messagebox.showinfo("Proceso Terminado", "Ya puedes realizar consultas SQL")

                # limpiar widgets en self.f_columns
                for widget in self.f_columns.winfo_children():
                    widget.destroy()

                insertar = True

            if insertar:
                self.refrescar()
                self.lbl_file_path_out.delete(0, tk.END)
                self.lbl_file_path_out.insert(0, file_path)

    def on_resize(self,event):
        ancho = self.winfo_width()
        self.TREE_item.column("item", width=int(ancho * 0.05), anchor="w")
        self.TREE_item.column("Query", width=int(ancho * 0.95), anchor="w")

    def on_row_selected(self,event):
        def show_data(columns, data):
            for widget in self.frm_response_show.winfo_children():
                widget.destroy()

            # Crear el Treeview
            self.tree = ttk.Treeview(self.frm_response_show, columns=tuple(columns), show="headings")
            self.tree.pack(expand=True, fill='both', padx=10, pady=10)

            # Configurar encabezados
            for col in columns:
                self.tree.heading(col, text=col)

            # Definir estilos de fila alternos usando tags
            self.tree.tag_configure('evenrow', background='#f0f0f0')  # gris claro
            self.tree.tag_configure('oddrow', background='white')     # blanco

            # Insertar datos con colores alternos
            for idx, row in enumerate(data):
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                self.tree.insert("", "end", values=row, tags=(tag,))
        # Obtener referencia al widget
        self.tree = event.widget  
        
        # Obtener el item seleccionado
        selected_item = self.tree.selection()
        if selected_item:
            item = selected_item[0]
            valores = self.tree.item(item, "values")
            print(f"Fila seleccionada: {valores[0]}",varsco["DATA_EXECUTE"][int(valores[0])-1])
            
            if len(varsco["DATA_EXECUTE"][int(valores[0])-1]) == 3 and varsco["DATA_EXECUTE"][int(valores[0])-1][1] != "Error":
                
                for i in varsco["DATA_EXECUTE"][int(valores[0])-1]:
                    print(i)
                show_data(varsco["DATA_EXECUTE"][int(valores[0])-1][2],varsco["DATA_EXECUTE"][int(valores[0])-1][1])
    
    def on_mouse_wheel(self,event):
        """Función para permitir que ambos Text se desplacen con la rueda del ratón"""
        delta = -1 * (event.delta // 120)
        # Si el evento se genera en el widget texto, desplazamos ambos
        if event.widget == self.texto:
            self.item_numbers.yview_scroll(int(delta), "units")
        elif event.widget == self.item_numbers:
           self.texto.yview_scroll(int(delta), "units")

    def actualizar_scroll(self,event):
        """Ajustar el área de scroll cuando self.f_columns cambie"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def al_seleccionar_hoja(self,event):
        self.BTN_CHARGE_DATA.config(state="normal")
        for widget in self.f_columns.winfo_children():
            widget.destroy()
        # self.f_columns = Frame(FR_content_frame)
        # self.f_columns.grid(row=4, column=0, columnspan=2)
        seleccion = self.list_sheets.get()  # Obtener el valor seleccionado

        if varsco["extension_user"] == '.xlsx':
            sheet = varsco["workbook"][seleccion]
            # Leer la primera fila (títulos)
            #first_line = [cell.value for cell in sheet[1]]
            first_line = [cell.value for cell in sheet[1] if cell.value and str(cell.value).strip() != ""]
        elif varsco["extension_user"] == '.xls':
            hojas = varsco["workbook"].sheet_by_name(seleccion)
            #first_line = hojas.row_values(0)
            first_line = [value for value in hojas.row_values(0) if value and str(value).strip() != ""]
        else:
            raise ValueError("Formato de archivo no soportado: usa .xls o .xlsx")
        
        rows = 0
        columns = 1
        for i in first_line:
            Label(self.f_columns, text=f"{i} :").grid(row=rows, column=columns - 1, sticky='e')
            Entry(self.f_columns).grid(row=rows, column=columns)
            rows += 1
            if rows == 6:
                rows = 0
                columns += 2
        # Asignar valores por defecto a los Entry
        rows = 0
        for widget in self.f_columns.winfo_children():
            if isinstance(widget, Entry):
                widget.insert(0, first_line[rows] if rows < len(first_line) else "")
                rows += 1

    def cambiar_texto(self):
        """Cambiar el texto del Checkbutton según su estado"""
        if varsco["var"].get():
            # varsco["var"] = True
            self.checkbutton.config(text="Yes")  # Si está seleccionado, mostrar "Sí"
            self.list_sheets.config(state='disabled')
            self.table_name.config(state='disabled')
            self.BTN_CHARGE_DATA.config(state="normal")
            try:
                for widget in self.f_columns.winfo_children():
                    widget.configure(state='disabled')
            except:
                pass  # Si el widget no tiene la opción 'state'
        else:
            # varsco["var"] = False
            self.checkbutton.config(text="No")   # Si no está seleccionado, mostrar "No"
            self.list_sheets.config(state='readonly')
            self.table_name.config(state='normal')
            try:
                for widget in self.f_columns.winfo_children():
                    widget.configure(state='normal')
            except:
                pass  # Si el widget no tiene la opción 'state'

    def cambiar_texto_save(self):
        """Cambiar el texto del Checkbutton según su estado"""
        if varsco["var_saved"].get():
            # varsco["var_saved"] = True
            self.checkbutton_save.config(text="Yes")  # Si está seleccionado, mostrar "Sí"
        else:
            # varsco["var_saved"] = False
            self.checkbutton_save.config(text="No")   # Si no está seleccionado, mostrar "No"
    
    def get_database_info(self,tree):
        # Limpiar todos los elementos
        for item in tree.get_children():
            tree.delete(item)
        # Conectar a la base de datos
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # db_path = os.path.join(base_dir, "DATA", "data_main.db")
        # conn = sqlite3.connect(db_path)
        conn = sqlite3.connect("DATA/data_main.db")
        cursor = conn.cursor()

        # Ejecutar la consulta para obtener las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        # Obtener los nombres de las tablas
        tablas = cursor.fetchall()

        data_main = []
        for tabla in tablas:
            data=[]
            # Consultar la estructura de la tabla
            cursor.execute(f"PRAGMA table_info({tabla[0]});")
            # Obtener los nombres de las columnas
            columnas = cursor.fetchall()
            # sum_columns = len(columnas)
            for j in columnas:
                #(9, 'name_column', 'TEXT')
                # data.append((j[0],j[1],j[2]))
                data.append((str(j[0]),j[1]))
            data_main.append((tabla[0],f"{len(columnas)} columnas",data))
        # return data_main
        # print
        # Insertar nodos padres e hijos dinámicamente
        for nombre, rows, hijos, *tag in data_main:
            tag = tag[0] if tag else "padre"  # Si hay un tag especial, lo usa; de lo contrario, "padre"
            padre_id = tree.insert("", "end", values=(nombre, rows), tags=(tag,))
            
            for item, fecha in hijos:
                tree.insert(padre_id, "end", values=(item, fecha, ""), tags=("hijo",))
        conn.close()

    def refrescar(self):
        self.checkbutton.config(text="No")   # Si no está seleccionado, mostrar "No"
        # varsco["var"]= False
        self.list_sheets.config(state='readonly')
        self.table_name.config(state='normal')
        # Muestra la notificación
        try:
            
            for widget in self.f_columns.winfo_children():
                widget.destroy()
            self.f_columns.update_idletasks()  # Fuerza la actualización de la interfaz
        except:
                pass  # Si el widget no tiene la opción 'state'
        self.table_name.delete(0, END)
        self.sufijo_name.delete(0, END)
        self.BTN_CHARGE_DATA.config(state="normal")
        self.list_sheets.set('')
        self.get_database_info(self.tree)

    def marcar_palabras(self,event=None):
        """Función para marcar palabras específicas"""
        
        # Limpiar cualquier formato anterior
        self.texto.tag_remove("resaltado", "1.0", END)
        
        # Obtener el contenido del texto
        texto_content = self.texto.get("1.0", END)
        
        # Recorrer cada palabra a resaltar
        for palabra in varsco["RESERVED_WORDS"]:
            # Usar expresión regular para encontrar solo palabras completas (ignorando mayúsculas/minúsculas)
            pattern = r'\b' + re.escape(palabra) + r'\b'  # \b asegura que sea una palabra completa
            matches = list(re.finditer(pattern, texto_content, re.IGNORECASE))  # Añadir re.IGNORECASE
            
            # Marcar cada coincidencia
            for match in matches:
                start_pos = self.texto.index(f"1.0 + {match.start()} chars")  # Convertir la posición a formato Tkinter
                end_pos = self.texto.index(f"1.0 + {match.end()} chars")  # Calcular el final
                self.texto.tag_add("resaltado", start_pos, end_pos)  # Agregar el tag para resaltar

        # Aplicar el color al tag "resaltado"
        self.texto.tag_configure("resaltado", foreground="orange")  # Cambiar el color a rojo
        
        ultima_linea = [int(self.item_numbers.index('end-1c').split('.')[0]), int(self.texto.index('end-1c').split('.')[0])]  # 'end-1c' elimina el carácter de nueva línea al final
        # Dividir la última línea para obtener el número de línea
        print(ultima_linea)
        if ultima_linea[1] != ultima_linea[0]:
            self.item_numbers.config(state="normal")
            self.item_numbers.delete(2.0, END)
            for i in range(2,ultima_linea[1]+1):
                self.item_numbers.insert(END,f"\n{i}")
            self.item_numbers.config(state="disabled")
if __name__ == "__main__":
    app = MiAplicacion()
    app.mainloop()
