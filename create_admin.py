from db_config import get_connection
from werkzeug.security import generate_password_hash

conn = get_connection()

cursor = conn.cursor()

cursor.execute(
    "INSERT INTO admin(email, password) VALUES(%s, %s)",
    (
        "admin@gmail.com",
        generate_password_hash("admin123")
    )
)

conn.commit()

conn.close()

print("Admin created successfully!")