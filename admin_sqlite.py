import sqlite3

# Conexión a la base (puede ser db.sqlite3 de Django o una propia)
conexion = sqlite3.connect("XLSQLQuery/DATA/data_main.db")
cursor = conexion.cursor()


# --- 1. Crear tabla temporal con SELECT ---
cursor.execute("DROP TABLE IF EXISTS atmp_data_test")
cursor.execute("""
CREATE TEMP TABLE atmp_data_test AS
SELECT inv_codart,inv_stkact,inv_stkaux FROM wms_inventory
""")

# --- 2. Consultar desde la temporal con una condición ---
cursor.execute("""WITH metadatos_cte AS (     SELECT DISTINCT usercode, username     FROM sun_usuarios     LIMIT 5 ) SELECT * FROM metadatos_cte""")
filas = cursor.fetchall()

print("Empleados con salario > 2000:")
for fila in filas:
    print(fila)

# Cerrar conexión
conexion.close()