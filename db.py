from libsql_client import Client

def db_config():
    turso_database_url = os.environ.get("TURSO_DATABASE_URL")
    turso_auth_token = os.environ.get("TURSO_AUTH_TOKEN")

    if not turso_database_url or not turso_auth_token:
        raise ValueError("Las variables TURSO_DATABASE_URL o TURSO_AUTH_TOKEN no están configuradas")

    # Crear cliente de conexión
    client = Client(
        url=turso_database_url,
        auth_token=turso_auth_token
    )

    return client
