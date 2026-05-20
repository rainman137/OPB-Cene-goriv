import psycopg2

conn = psycopg2.connect(
    host="baza.fmf.uni-lj.si",
    dbname="sem2026_dezmal",
    user="dezmal",     # ← your university username
    password="lpzb73vw"  # ← your university password
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM regija;")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
print("Povezava uspešna!")