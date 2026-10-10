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
            
        db.commit()
        if devuelve:
            return cursor.fetchone()
        return cursor.rowcount
    except psycopg.errors.ForeignKeyViolation:
        db.rollback()
        print("Error FK ")
    except psycopg.errors.UniqueViolation:
        db.rollback()
        print("Error Unique")
    except psycopg.Error as e:
        db.rollback()
        print("ocurrio un error en la base de datos. ")
        print(e)
    finally:
        cursor.close()
 