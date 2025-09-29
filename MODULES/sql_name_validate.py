import re
from MODULES.vars import varsco
def name_validate_sql(name):
    # 1. Verificar que el nombre no esté vacío
    if not name:
        return False, f"[{name}] no debe ser un valor nulo"
    # 2. Verificar que el nombre no comience con un número
    if name[0].isdigit():
        return False, f"[{name}] no puede comenzar con un número."
    # 3. Verificar que el nombre no contenga espacios
    if " " in name:
        return False, f"[{name}] contiene espacios"
    # 4. Verificar que el nombre no contenga caracteres especiales no permitidos
    if not re.match("^[a-zA-Z0-9_]+$", name):
        return False, f"[{name}] solo debe contener letras, números(nunca al inicio del nombre) y guiones bajos, elimina los caracteres no permitidos"
    # 5. Verificar que el nombre no sea una palabra reservada
    if name.lower() in varsco["RESERVED_WORDS"]:
        return False, f"No se puede usar [{name}] porque es una palabra reservada"
    return True, f"[{name}] OK"