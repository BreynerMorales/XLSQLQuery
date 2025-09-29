import sqlite3
from MODULES.vars import varsco
def execute_query(data_text, limite_select=10000):
    """
    Ejecuta un bloque con múltiples sentencias SQL.
    Devuelve una lista de resultados (uno por sentencia):
    - SELECT/PRAGMA → [sql, filas, columnas]
    - DML (INSERT, UPDATE, DELETE, REPLACE) → [sql, rowcount]
    - DDL (CREATE, DROP, ALTER) → [sql, True]
    - Error → [sql, "Error", mensaje_error]
    """
    query_no_comments=""
    for i in data_text.split("\n"):
        if i[0:2] != "--":
            query_no_comments +=  F" {i}"
        else:
            print(f"THIS IS A COMMENT: {i}")
    print("COMMENTS CLEANED",query_no_comments)
    bloque_sql = query_no_comments.replace("\n", " ").replace("\t", " ")
    conexion = sqlite3.connect("DATA/data_main.db")

    cursor = conexion.cursor()
    resultados = []

    # Separar sentencias por ;
    sentencias = [s.strip() for s in bloque_sql.split(";") if s.strip()]
    print("THIS IS A SENTENCES:",sentencias)
    for sql in sentencias:
        qtype = sql.split()[0].upper()
        print("THIS IS TYPE",qtype)
        try:
            cursor.execute(sql)

            if qtype in ("SELECT", "PRAGMA","WITH"):
                # filas = cursor.fetchall()
                filas = cursor.fetchmany(limite_select)
                columnas = [desc[0] for desc in cursor.description] if cursor.description else []
                resultados.append([sql, filas, columnas])
            elif qtype in ("INSERT", "UPDATE", "DELETE", "REPLACE"):
                resultados.append([sql, cursor.rowcount])
            else:
                resultados.append([sql, True])  # CREATE, DROP, ALTER, etc.
        except Exception as e:
            resultados.append([sql, "Error", str(e)])
    varsco["DATA_EXECUTE"] = resultados
    conexion.close()