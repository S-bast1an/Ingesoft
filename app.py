from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask.wrappers import Request
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from typing import cast, Dict, Any
from ejercicios_ia import generar_ejercicios_suma
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
db = SQLAlchemy(app)
login_manager = cast(LoginManager, LoginManager(app))
login_manager.login_view = 'login'  # type: ignore[assignment]

class ProgresoSuma(db.Model):  # type: ignore
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id'), nullable=False)
    nivel = Column(Integer, default=1)
    ejercicios_completados = Column(Integer, default=0)
    aciertos = Column(Integer, default=0)
    ultima_puntuacion = Column(Float, default=0.0)

    def __init__(self, usuario_id=None, nivel=1, ejercicios_completados=0, aciertos=0, ultima_puntuacion=0.0):
        self.usuario_id = usuario_id
        self.nivel = nivel
        self.ejercicios_completados = ejercicios_completados
        self.aciertos = aciertos
        self.ultima_puntuacion = ultima_puntuacion

class Usuario(UserMixin, db.Model):  # type: ignore
    __tablename__ = 'usuario'
    
    id = Column(Integer, primary_key=True)
    identidad = Column(String(20), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    progreso_suma = relationship('ProgresoSuma', backref='usuario', lazy='dynamic')

    __table_args__ = {'extend_existing': True}

    def __init__(self, identidad=None, password=None):
        self.identidad = identidad
        self.password = password

    def get_progreso_suma(self):
        if not self.progreso_suma.first():
            nuevo_progreso = ProgresoSuma(usuario_id=self.id)
            db.session.add(nuevo_progreso)
            db.session.commit()
            return nuevo_progreso
        return self.progreso_suma.first()

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identidad = request.form.get('identidad')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(identidad=identidad).first()
        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas. Por favor, intenta de nuevo.', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/primaria/<tema>')
@login_required
def primaria(tema):
    temas = {
        'operaciones-basicas': {
            'titulo': 'Operaciones Básicas',
            'operaciones': {
                'suma': 'Suma',
                'resta': 'Resta',
                'multiplicacion': 'Multiplicación',
                'division': 'División'
            }
        },
        'fracciones-decimales': 'Fracciones y Decimales',
        'numeros-naturales': 'Números Naturales',
        'tablas-multiplicar': 'Tablas de Multiplicar'
    }
    
    if tema not in temas:
        flash('Tema no encontrado', 'error')
        return redirect(url_for('dashboard'))
        
    titulo = temas[tema] if isinstance(temas[tema], str) else temas[tema]['titulo']
    operaciones = temas[tema].get('operaciones') if isinstance(temas[tema], dict) else None
    
    return render_template('temas/primaria.html', 
                         tema=tema, 
                         titulo=titulo,
                         operaciones=operaciones)

@app.route('/secundaria/<tema>')
@login_required
def secundaria(tema):
    temas = {
        'algebra': 'Álgebra',
        'geometria': 'Geometría',
        'trigonometria': 'Trigonometría',
        'estadistica': 'Estadística Básica',
        'funciones': 'Funciones y Gráficas'
    }
    if tema not in temas:
        flash('Tema no encontrado', 'error')
        return redirect(url_for('dashboard'))
    return render_template('temas/secundaria.html', tema=tema, titulo=temas[tema])

@app.route('/ejercicios/<tipo>')
@login_required
def ejercicios(tipo):
    tipos = {
        'ejemplos': 'Ejemplos Detallados',
        'interactivos': 'Ejercicios Interactivos',
        'evaluacion': 'Evaluación Continua'
    }
    if tipo not in tipos:
        flash('Tipo de ejercicio no encontrado', 'error')
        return redirect(url_for('dashboard'))
    return render_template('ejercicios/ejercicios.html', tipo=tipo, titulo=tipos[tipo])

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/primaria/operaciones-basicas/suma/ejercicios')
@login_required
def ejercicios_suma():
    progreso = current_user.get_progreso_suma()
    # Calcula los porcentajes aquí
    nivel_porcentaje = (progreso.nivel / 3) * 100
    precision_porcentaje = (progreso.aciertos / progreso.ejercicios_completados * 100) if progreso.ejercicios_completados > 0 else 0
    return render_template('ejercicios/suma.html', 
                         nivel=progreso.nivel,
                         ejercicios_completados=progreso.ejercicios_completados,
                         aciertos=progreso.aciertos,
                         nivel_porcentaje=nivel_porcentaje,
                         precision_porcentaje=precision_porcentaje)

@app.route('/api/ejercicios/suma')
@login_required
def obtener_ejercicios_suma():
    progreso = current_user.get_progreso_suma()
    ejercicios = generar_ejercicios_suma(nivel=progreso.nivel)
    return jsonify(ejercicios)

@app.route('/api/ejercicios/suma/verificar', methods=['POST'])
@login_required
def verificar_ejercicio_suma():
    data = cast(Dict[str, Any], request.json)  # type: ignore
    respuesta_usuario = int(data.get('respuesta', 0))
    respuesta_correcta = int(data.get('respuesta_correcta', 0))
    tiempo = float(data.get('tiempo', 0))  # Tiempo en segundos
    
    progreso = current_user.get_progreso_suma()
    progreso.ejercicios_completados += 1
    
    correcto = respuesta_usuario == respuesta_correcta
    if correcto:
        progreso.aciertos += 1
    
    # Registrar resultado en la IA
    from ejercicios_ia import generador
    generador.registrar_resultado(correcto, tiempo)
    
    # Calcular puntuación
    puntuacion = (progreso.aciertos / progreso.ejercicios_completados) * 100
    progreso.ultima_puntuacion = puntuacion
    
    nivel_anterior = progreso.nivel
    
    # Actualizar nivel basado en el rendimiento y el árbol de decisión
    dificultad = generador.ia.predecir_dificultad(progreso.nivel)
    
    # Determinar el nuevo nivel basado en la dificultad
    if dificultad >= 1.8 and progreso.nivel < 3:
        progreso.nivel += 1
        print(f"Subiendo a nivel {progreso.nivel}")
    elif dificultad <= 0.6 and progreso.nivel > 1:
        progreso.nivel -= 1
        print(f"Bajando a nivel {progreso.nivel}")
    
    # Si el nivel cambió, reiniciar contadores
    if progreso.nivel != nivel_anterior:
        progreso.ejercicios_completados = 0
        progreso.aciertos = 0
    
    db.session.commit()
    
    # Devolver toda la información necesaria para actualizar la UI
    return jsonify({
        'correcto': correcto,
        'nivel': progreso.nivel,
        'nivel_cambio': progreso.nivel != nivel_anterior,
        'puntuacion': puntuacion,
        'ejercicios_completados': progreso.ejercicios_completados,
        'aciertos': progreso.aciertos,
        'tiempo': tiempo,
        'mensaje_ayuda': generador.mensaje_ayuda
    })

@app.route('/api/ejercicios/suma/reiniciar', methods=['POST'])
@login_required
def reiniciar_progreso_suma():
    # Reiniciar el progreso en la base de datos
    progreso = current_user.get_progreso_suma()
    progreso.nivel = 1
    progreso.ejercicios_completados = 0
    progreso.aciertos = 0
    progreso.ultima_puntuacion = 0.0
    db.session.commit()
    
    # Reiniciar completamente el generador de ejercicios
    from ejercicios_ia import generador
    generador.reiniciar()
    
    flash('¡Progreso reiniciado exitosamente!', 'success')
    return jsonify({
        'success': True,
        'ejercicios': generar_ejercicios_suma(nivel=1)  # Generar nuevos ejercicios de nivel 1
    })

@app.route('/api/ejercicios/suma/configurar', methods=['POST'])
@login_required
def configurar_ejercicios_suma():
    try:
        data = json.loads(cast(str, request.get_data(as_text=True)))
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se recibieron datos JSON válidos'
            }), 400
            
        ejercicios_requeridos = data.get('ejercicios_requeridos')
        if ejercicios_requeridos is None:
            return jsonify({
                'success': False,
                'error': 'Falta el parámetro ejercicios_requeridos'
            }), 400
            
        ejercicios_requeridos = int(ejercicios_requeridos)
        
        # Validar el rango de ejercicios requeridos
        if not 1 <= ejercicios_requeridos <= 10:
            return jsonify({
                'success': False,
                'error': 'El número de ejercicios debe estar entre 1 y 10'
            }), 400
        
        # Obtener el progreso actual del usuario
        progreso = current_user.get_progreso_suma()
        nivel_actual = progreso.nivel
        
        # Configurar el generador usando el nivel actual
        from ejercicios_ia import generador
        generador.ia.configurar(ejercicios_requeridos)
        generador.ia.nivel_actual = nivel_actual  # Establecer el nivel actual
        
        return jsonify({
            'success': True,
            'mensaje': f'Configuración actualizada a {ejercicios_requeridos} ejercicios',
            'nivel_actual': nivel_actual
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'El valor proporcionado no es un número válido'
        }), 400
    except Exception as e:
        app.logger.error(f'Error al configurar ejercicios: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@app.route('/primaria/operaciones-basicas/resta/ejercicios')
@login_required
def ejercicios_resta():
    # Debes crear la plantilla 'ejercicios/resta.html' o usar una existente
    # y pasarle los datos necesarios, similar a ejercicios_suma
    progreso = current_user.get_progreso_resta()  # Debes tener este método
    return render_template('ejercicios/resta.html',
                          nivel=progreso.nivel,
                          ejercicios_completados=progreso.ejercicios_completados,
                          aciertos=progreso.aciertos)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 