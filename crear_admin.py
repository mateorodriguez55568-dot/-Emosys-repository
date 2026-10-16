from werkzeug.security import generate_password_hash

password = "Admin123"

hash_password = generate_password_hash(password)

print(hash_password)
