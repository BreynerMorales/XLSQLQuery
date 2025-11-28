#!/usr/bin/env python3
"""
csv_paths_reader_with_sqlite.py
Interfaz gráfica para seleccionar una carpeta y listar/imprimir las rutas
de todos los archivos .csv encontrados (recursivamente).
Además permite convertir todos los CSV encontrados en tablas dentro de
una única base de datos SQLite, validando nombres y tipos de columnas.
"""

import os
import sys
import platform
import subprocess
import sqlite3
import csv
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# -------------------------
# Funciones utilitarias
# -------------------------
def find_csv_files(folder: Path, recursive: bool = True):
    if recursive:
        return sorted(folder.rglob("*.csv"))
    else:
        return sorted(folder.glob("*.csv"))

def print_to_system_printer(text: str, job_name: str = "CSV paths print job"):
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tf:
        tf.write(text)
        tmp_path = tf.name

    current_platform = platform.system()
    try:
        if current_platform == "Windows":
            os.startfile(tmp_path, "print")
        elif current_platform in ("Linux", "Darwin"):
            subprocess.run(["lpr", "-P", "default", tmp_path], check=True)
        else:
            raise RuntimeError(f"Plataforma no soportada para impresión: {current_platform}")
    finally:
        pass

# -------------------------
# Utilidades para SQLite
# -------------------------
def normalizar_nombre(nombre: str) -> str:
    # Quitar BOM, recortar, sustituir espacios y caracteres no válidos por _
    if nombre is None:
        nombre = ""
    nombre = nombre.strip()
    # Reemplazar caracteres no alfanuméricos por _
    import re
    nombre = re.sub(r'[^\w]', '_', nombre, flags=re.UNICODE)
    # Si empieza con dígito, prefijar _
    if len(nombre) == 0:
        nombre = "col"
    if nombre[0].isdigit():
        nombre = "_" + nombre
    return nombre

def es_numerico_str(s: str) -> bool:
    if s is None:
        return False
    s = s.strip()
    if s == "":
        return False
    try:
        float(s)
        return True
    except:
        return False

def detectar_tipo_columna(valores):
    # valores: iterable de strings (ya leídos)
    # ignorar strings vacíos para la detección
    validos = [v for v in valores if v is not None and v.strip() != ""]
    if not validos:
        return "TEXT"
    for v in validos:
        if not es_numerico_str(v):
            return "TEXT"
    return "NUMERIC"

def convertir_valor_segun_tipo(valor, tipo):
    if valor is None:
        return None
    s = valor.strip()
    if s == "":
        return None
    if tipo == "NUMERIC":
        try:
            # intentar int si no tiene punto, sino float
            if '.' in s or 'e' in s or 'E' in s:
                return float(s)
            else:
                return int(float(s))
        except:
            try:
                return float(s)
            except:
                return None
    else:
        return s

# -------------------------
# GUI
# -------------------------
# class CSVReaderApp(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("Lector de rutas CSV & Converter")
#         self.geometry("1000x650")
#         self.minsize(800, 480)

#         self.folder_path = None
#         self.csv_paths = []

#         self._create_widgets()
#         self._layout_widgets()
class CSVReaderApp(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Ya NO se usa self.title ni geometry
        # porque esto ya NO es una ventana
        # sino un frame embebible

        self.parent = parent
        self.folder_path = None
        self.csv_paths = []

        # Crear widgets en este frame
        self._create_widgets()
        self._layout_widgets()

        # Expandir correctamente
        self.pack(side="left",fill="both", expand=True)
    def _create_widgets(self):
        # Barra superior de controles
        self.frame_controls = ttk.Frame(self)

        self.btn_select_folder = ttk.Button(self.frame_controls, text="Select file", command=self.on_select_folder)
        self.lbl_folder = ttk.Label(self.frame_controls, text="Ninguna carpeta seleccionada", anchor="w")

        self.chk_recursive_var = tk.BooleanVar(value=True)
        self.chk_recursive = ttk.Checkbutton(self.frame_controls, text="recursive search", variable=self.chk_recursive_var)

        self.btn_scan = ttk.Button(self.frame_controls, text="Find files CSV", command=self.on_scan)
        self.btn_clear = ttk.Button(self.frame_controls, text="List clear", command=self.on_clear)

        # Área central: Listbox + Text preview
        self.paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)

        # Listbox con scrollbar (lista de rutas)
        #self.frame_list = ttk.Labelframe(self.paned, text="Archivos encontrados")
        #self.listbox = tk.Listbox(self.frame_list, selectmode=tk.EXTENDED)
        #self.sb_list = ttk.Scrollbar(self.frame_list, orient=tk.VERTICAL, command=self.listbox.yview)
        #self.listbox.configure(yscrollcommand=self.sb_list.set)

        # Previsualización / textarea
        self.frame_preview = ttk.Labelframe(self.paned, text="Preview (Path)")
        self.text_preview = tk.Text(self.frame_preview, wrap="none", height=10)
        self.sb_text_v = ttk.Scrollbar(self.frame_preview, orient=tk.VERTICAL, command=self.text_preview.yview)
        self.sb_text_h = ttk.Scrollbar(self.frame_preview, orient=tk.HORIZONTAL, command=self.text_preview.xview)
        self.text_preview.configure(yscrollcommand=self.sb_text_v.set, xscrollcommand=self.sb_text_h.set)

        # Botones de acción inferior
        self.frame_actions = ttk.Frame(self)
        self.btn_save = ttk.Button(self.frame_actions, text="Save list (.txt)", command=self.on_save)
        self.btn_print = ttk.Button(self.frame_actions, text="Print Path", command=self.on_print)
        self.btn_copy = ttk.Button(self.frame_actions, text="Copy clipboard", command=self.on_copy)
        self.btn_convert = ttk.Button(self.frame_actions, text="DATA LOAD", command=self.on_convert_all)
        self.lbl_count = ttk.Label(self.frame_actions, text="0 archivos encontrados")
        self.lbl_status = ttk.Label(self.frame_actions, text="Status: OK", anchor="w")

    def _layout_widgets(self):
        # Top controls
        self.frame_controls.pack(fill="x", padx=12, pady=10)
        self.btn_select_folder.pack(side="left")
        self.lbl_folder.pack(side="left", padx=10, fill="x", expand=True)
        self.chk_recursive.pack(side="left", padx=8)
        self.btn_scan.pack(side="left", padx=6)
        self.btn_clear.pack(side="left", padx=6)

        # Paned content
        self.paned.pack(fill="both", expand=True, padx=12, pady=(0,12))

        # List frame layout
        #self.paned.add(self.frame_list, weight=1)
        #self.listbox.pack(side="left", fill="both", expand=True, padx=(8,0), pady=8)
        #self.sb_list.pack(side="left", fill="y", padx=(0,8), pady=8)

        # Preview frame layout
        self.paned.add(self.frame_preview, weight=2)
        self.text_preview.pack(fill="both", expand=True, padx=(8,0), pady=(8,0))
        self.sb_text_v.pack(side="right", fill="y", pady=(8,0))
        self.sb_text_h.pack(side="bottom", fill="x", pady=(0,8))

        # Actions layout
        self.frame_actions.pack(fill="x", padx=12, pady=(0,12))
        self.btn_save.pack(side="left")
        self.btn_print.pack(side="left", padx=8)
        self.btn_copy.pack(side="left", padx=8)
        self.btn_convert.pack(side="left", padx=8)
        self.lbl_count.pack(side="right")
        self.lbl_status.pack(side="left", padx=12)

    # -------------------------
    # Callbacks
    # -------------------------
    def on_select_folder(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta donde buscar archivos CSV")
        if folder:
            self.folder_path = Path(folder)
            self.lbl_folder.config(text=str(self.folder_path))

    def on_scan(self):
        if not self.folder_path:
            messagebox.showwarning("Carpeta no seleccionada", "Selecciona primero una carpeta.")
            return

        recursive = bool(self.chk_recursive_var.get())
        self.csv_paths = [str(p) for p in find_csv_files(self.folder_path, recursive=recursive)]
        self._update_list_and_preview()

    def on_clear(self):
        self.csv_paths = []
        self.folder_path = None
        self.lbl_folder.config(text="Ninguna carpeta seleccionada")
        #self.listbox.delete(0, tk.END)
        self.text_preview.delete("1.0", tk.END)
        self.lbl_count.config(text="0 archivos encontrados")
        self.lbl_status.config(text="Estado: listo")

    def on_save(self):
        if not self.csv_paths:
            messagebox.showinfo("Sin archivos", "No hay rutas para guardar.")
            return
        save_path = filedialog.asksaveasfilename(
            title="Guardar lista de rutas como",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            initialfile="csv_paths.txt"
        )
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    for p in self.csv_paths:
                        f.write(p + "\n")
                messagebox.showinfo("Guardado", f"Lista guardada en:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error al guardar", str(e))

    def on_print(self):
        if not self.csv_paths:
            messagebox.showinfo("Sin archivos", "No hay rutas para imprimir.")
            return
        text = "\n".join(self.csv_paths)
        try:
            print_to_system_printer(text)
            messagebox.showinfo("Impresión", "Trabajo de impresión enviado al sistema (si está disponible).")
        except Exception as e:
            messagebox.showerror("Error al imprimir", f"No se pudo imprimir: {e}")

    def on_copy(self):
        if not self.csv_paths:
            messagebox.showinfo("Sin archivos", "No hay rutas para copiar.")
            return
        text = "\n".join(self.csv_paths)
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copiado", "Rutas copiadas al portapapeles.")

    def _update_list_and_preview(self):
        #self.listbox.delete(0, tk.END)
        #for p in self.csv_paths:
        #    self.listbox.insert(tk.END, p)

        self.text_preview.delete("1.0", tk.END)
        if self.csv_paths:
            self.text_preview.insert(tk.END, "\n".join(self.csv_paths))
        else:
            self.text_preview.insert(tk.END, "No se encontraron archivos .csv en la carpeta seleccionada.")

        self.lbl_count.config(text=f"{len(self.csv_paths)} archivos encontrados")

    # -------------------------
    # Conversión CSV -> SQLite
    # -------------------------
    def on_convert_all(self):
        if not self.csv_paths:
            messagebox.showwarning("Sin archivos", "Primero busca y selecciona una carpeta con archivos CSV.")
            return

        db_path = filedialog.asksaveasfilename(
            title="Selecciona o crea la base de datos SQLite donde guardar tablas",
            defaultextension=".sqlite",
            filetypes=[("SQLite", "*.sqlite"), ("Todos", "*.*")]
        )
        if not db_path:
            return

        self.lbl_status.config(text="Estado: procesando...")
        self.update_idletasks()

        errors = []
        processed = 0

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for csv_file in self.csv_paths:
                try:
                    p = Path(csv_file)
                    table_name = normalizar_nombre(p.stem)

                    # Leer archivo CSV y detectar dialecto
                    with open(p, "r", newline='', encoding="utf-8") as fh:
                        sample = fh.read(2048)
                        fh.seek(0)
                        try:
                            dialect = csv.Sniffer().sniff(sample)
                        except Exception:
                            dialect = csv.get_dialect('excel')
                        reader = csv.reader(fh, dialect)

                        rows = list(reader)

                    if not rows:
                        errors.append(f"{p.name}: archivo vacío")
                        continue

                    # Encabezados
                    raw_headers = rows[0]
                    headers = [normalizar_nombre(h) for h in raw_headers]

                    # Asegurar que no haya columnas duplicadas (añadir sufijos si es necesario)
                    seen = {}
                    for i, h in enumerate(headers):
                        base = h or f"col{i}"
                        if base in seen:
                            seen[base] += 1
                            headers[i] = f"{base}_{seen[base]}"
                        else:
                            seen[base] = 0
                            headers[i] = base

                    # Transponer filas para detectar tipos por columna (saltando cabecera)
                    data_rows = rows[1:]
                    if not data_rows:
                        # No hay filas de datos, crear columnas como TEXT por defecto
                        tipos = ["TEXT"] * len(headers)
                    else:
                        # Preparar columnas como listas
                        cols = [[] for _ in headers]
                        for r in data_rows:
                            # Si fila más corta, extender con ""
                            r_extended = list(r) + [""] * (len(headers) - len(r))
                            for idx, val in enumerate(r_extended[:len(headers)]):
                                cols[idx].append(val if val is not None else "")

                        tipos = [detectar_tipo_columna(col) for col in cols]

                    # Crear tabla (DROP IF EXISTS para reemplazar)
                    col_defs = ", ".join(f'"{headers[i]}" {tipos[i]}' for i in range(len(headers)))
                    cursor.execute(f'PRAGMA foreign_keys = OFF;')
                    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')
                    cursor.execute(f'CREATE TABLE "{table_name}" ({col_defs});')
                    print(f'CREATE TABLE "{table_name}" ({col_defs});')
                    # Insertar filas válidas
                    placeholders = ", ".join("?" for _ in headers)
                    # insert_sql = (
                    #     f'INSERT INTO "{table_name}" '
                    #     f'({", ".join(f"""\"{h}\"""" for h in headers)}) '
                    #     f'VALUES ({placeholders});'
                    # )
                    columns = ", ".join(['"{}"'.format(h) for h in headers])

                    insert_sql = (
                        f'INSERT INTO "{table_name}" ({columns}) '
                        f'VALUES ({placeholders});'
                    )
                    print(insert_sql)
                    inserted = 0
                    for r in data_rows:
                        # Extender fila si es más corta
                        r_extended = list(r) + [""] * (len(headers) - len(r))
                        # Si fila está completamente vacía -> saltar
                        if all((cell is None or str(cell).strip() == "") for cell in r_extended[:len(headers)]):
                            continue
                        # Convertir valores según tipos
                        valores_insert = []
                        for idx, raw_val in enumerate(r_extended[:len(headers)]):
                            tipo = tipos[idx]
                            valor_conv = convertir_valor_segun_tipo(raw_val, tipo)
                            valores_insert.append(valor_conv)
                        try:
                            cursor.execute(insert_sql, valores_insert)
                            inserted += 1
                        except Exception as e:
                            # Si un insert falla, registrar y seguir
                            errors.append(f"{p.name}: error insert fila -> {e}")
                            continue

                    conn.commit()
                    processed += 1

                except Exception as e_file:
                    errors.append(f"{csv_file}: {e_file}")
                    continue

        except Exception as e_conn:
            messagebox.showerror("Error BD", f"No se pudo crear/abrir la base de datos:\n{e_conn}")
            self.lbl_status.config(text="Estado: error")
            return
        finally:
            try:
                conn.close()
            except:
                pass

        # Mostrar resumen
        summary = f"Procesados: {processed} archivos.\n"
        print(summary)
        if errors:
            summary += "\nErrores:\n" + "\n".join(errors)
            messagebox.showwarning("Proceso completado con errores", summary)
            self.lbl_status.config(text="Estado: completado (con errores)")
        else:
            messagebox.showinfo("Proceso completado", summary)
            self.lbl_status.config(text="Estado: Succesfull")

    # Fin on_convert_all

# -------------------------
# Main
# -------------------------
# def main():
#     app = CSVReaderApp()
#     app.mainloop()
def main(parent_frame):
    CSVReaderApp(parent_frame)

# if __name__ == "__main__":
#     main()
