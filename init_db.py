from app import app, db, Usuario
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Crear las tablas
        db.create_all()
        
        # Verificar si el usuario ya existe
        usuario = Usuario.query.filter_by(identidad='123').first()
        if not usuario:
            # Crear usuario de prueba
            nuevo_usuario = Usuario(
                identidad='123',
                password=generate_password_hash('123')
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            print("Usuario de prueba creado exitosamente")
        else:
            print("El usuario de prueba ya existe")

if __name__ == '__main__':
    init_db() 