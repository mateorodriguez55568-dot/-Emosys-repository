from werkzeug.security import generate_password_hash

clave = "Admin1234"

hash_generado = generate_password_hash(clave)

print(hash_generado)