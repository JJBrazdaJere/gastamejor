import psycopg

def conectar_db (host, port, dbname, user, password):
    
    conexion = psycopg.connect(
    host=host,
    port=port,
    dbname=dbname,
    user =user,
    password= password
    )
    return conexion
