import os
from pathlib import Path
import sys

try:
    import mysql.connector
except Exception as e:
    print('Missing mysql-connector-python. Install with: pip install mysql-connector-python')
    raise

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / '.env'
SQL_PATH = ROOT / 'database' / 'schema.sql'

def load_env(path):
    data = {}
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        line=line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k,v = line.split('=',1)
            data[k.strip()] = v.strip()
    return data


def main():
    env = load_env(ENV_PATH)
    host = env.get('MYSQL_HOST','localhost')
    user = env.get('MYSQL_USER','root')
    password = env.get('MYSQL_PASSWORD','')
    db = env.get('MYSQL_DB')

    if not SQL_PATH.exists():
        print(f'SQL file not found: {SQL_PATH}')
        sys.exit(1)

    print(f'Connecting to MySQL at {host} as {user!r}...')
    conn = mysql.connector.connect(host=host, user=user, password=password)
    cursor = conn.cursor()

    sql = SQL_PATH.read_text()
    print('Executing SQL (this may take a few seconds)...')
    try:
        for result in cursor.execute(sql, multi=True):
            if result.with_rows:
                print(f'Result: {result.rowcount} rows')
            else:
                print(f'Executed: {result.statement[:80]}' )
        conn.commit()
    except Exception as e:
        print('Error executing SQL:', e)
        conn.rollback()
        cursor.close()
        conn.close()
        sys.exit(1)

    # Verify counts
    if db:
        conn_db = mysql.connector.connect(host=host, user=user, password=password, database=db)
        cur2 = conn_db.cursor()
        try:
            cur2.execute('SELECT COUNT(*) FROM users')
            users_count = cur2.fetchone()[0]
            cur2.execute('SELECT COUNT(*) FROM products')
            prod_count = cur2.fetchone()[0]
            print(f'Verified: users={users_count}, products={prod_count}')
        except Exception as e:
            print('Verification failed:', e)
        finally:
            cur2.close()
            conn_db.close()

    cursor.close()
    conn.close()
    print('Seeding complete.')

if __name__ == '__main__':
    main()
