import psycopg2

passwords = ["postgres_password", "postgres", "password", "root", "abc", "123", ""]
db_name = "ag_db"
user = "postgres"
host = "localhost"

for p in passwords:
    try:
        conn = psycopg2.connect(dbname=db_name, user=user, password=p, host=host)
        print(f"SUCCESS:{p}")
        conn.close()
        break
    except Exception as e:
        print(f"FAILED:{p}:{e}")
