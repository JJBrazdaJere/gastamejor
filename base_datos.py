import psycopg

def leer_db(db, sql,variable = None):
    cursor = db.cursor()
    try:
        if variable != None:
            cursor.execute(sql, variable)
        else:
            cursor.execute(sql)
        return cursor.fetchall()
    except psycopg.Error:
        db.rollback()
        print("ocurrio un error en la base de datos")
        return None
    finally:
        cursor.close()

def commit_db(db, sql,variable = None, devuelve= False):
    cursor = db.cursor()
    try:
        if variable != None:
            cursor.execute(sql, variable)
        else:
            cursor.execute(sql)

        # Leemos el resultado ANTES de confirmar. Es necesario para los INSERT
        # con "RETURNING id": si se confirma primero, el resultado puede perderse.
        resultado = cursor.fetchone() if devuelve else cursor.rowcount

        db.commit()
        return resultado
    except psycopg.errors.ForeignKeyViolation:
        db.rollback()
        print("Error: el registro relacionado no existe (clave foranea). ")
    except psycopg.errors.UniqueViolation:
        db.rollback()
        print("Error: ya existe un registro con ese valor unico (por ej. email duplicado). ")
    except psycopg.Error as e:
        db.rollback()
        print("ocurrio un error en la base de datos. ")
        print(e)
    finally:
        cursor.close()
 