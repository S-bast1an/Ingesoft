import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from sklearn.tree import DecisionTreeRegressor
from collections import deque
import random

class TrueAISystem:
    def __init__(self):
        # Modelo de IA (inicialmente vacío)
        self.model = None
        self.mensaje_ayuda = ""
        self.ejercicios_requeridos = 5  # Valor por defecto
        self.nivel_actual = 1  # Añadimos nivel actual
        
        # Almacenamiento de datos
        self.features = pd.DataFrame(columns=[
            'nivel', 
            'tasa_aciertos', 
            'tiempo_promedio', 
            'ejercicios_consecutivos',
            'fallos_consecutivos',
            'ejercicios_requeridos'
        ])
        self.targets = pd.Series(name='dificultad_optima')
        
        # Historial temporal para calcular características
        self.historial_reciente = deque(maxlen=5)  # Últimos 5 ejercicios
        self.fallos_consecutivos = 0

    def configurar(self, ejercicios_requeridos: int, nivel: Optional[int] = None):
        """Configura el número de ejercicios requeridos y opcionalmente el nivel"""
        self.ejercicios_requeridos = max(1, min(10, ejercicios_requeridos))
        if nivel is not None:
            self.nivel_actual = max(1, min(3, nivel))  # Asegurar que el nivel esté entre 1 y 3
        
    def registrar_resultado(self, nivel: int, correcto: bool, tiempo: float):
        """Registra un resultado y actualiza el modelo cuando hay suficientes datos"""
        self.nivel_actual = nivel  # Actualizamos el nivel actual
        
        # Actualizar contador de fallos
        if correcto:
            self.fallos_consecutivos = 0
        else:
            self.fallos_consecutivos += 1
            
        # Actualizar mensaje de ayuda
        if nivel == 1 and self.fallos_consecutivos >= self.ejercicios_requeridos:
            self.mensaje_ayuda = "No te preocupes si te resulta difícil. Es normal encontrar desafíos al aprender algo nuevo. ¿Qué tal si le pides ayuda a tu profesor? ¡Juntos pueden resolver esto!"
        else:
            self.mensaje_ayuda = ""

        # 1. Guardar resultado en historial reciente
        self.historial_reciente.append({
            'nivel': nivel,
            'correcto': correcto,
            'tiempo': tiempo
        })
        
        # 2. Calcular características actuales
        if len(self.historial_reciente) > 0:
            caracteristicas = self._calcular_caracteristicas(nivel)
            dificultad_optima = self._calcular_dificultad_optima(correcto, tiempo, nivel)
            
            # 3. Agregar a los datos de entrenamiento
            self.features = pd.concat([
                self.features,
                pd.DataFrame([caracteristicas])
            ], ignore_index=True)
            
            self.targets = pd.concat([
                self.targets,
                pd.Series([dificultad_optima])
            ], ignore_index=True)
            
            # 4. Entrenar modelo cuando tengamos suficientes datos
            if len(self.features) >= 10:  # Entrenar con mínimo 10 ejemplos
                self._entrenar_modelo()
    
    def predecir_dificultad(self, nivel: int) -> float:
        """Predice la dificultad óptima usando IA o reglas heurísticas si no hay modelo"""
        # Si hay demasiados fallos consecutivos y no es nivel 1, bajar nivel
        if self.fallos_consecutivos >= self.ejercicios_requeridos and nivel > 1:
            print(f"Prediciendo bajar de nivel por fallos consecutivos: {self.fallos_consecutivos}")
            return 0.5  # Factor para bajar de nivel
            
        if self.model is not None:
            # Usar modelo de IA
            caracs = self._calcular_caracteristicas(nivel)
            prediccion = self.model.predict([list(caracs.values())])[0]
            print(f"Predicción del modelo IA: {prediccion}")
            
            # Determinar cambio de nivel basado en la predicción
            if prediccion >= 1.8 and nivel < 3:
                print("Prediciendo subir de nivel por alto rendimiento")
                return 2.0  # Subir nivel
            elif prediccion <= 0.6 and nivel > 1:
                print("Prediciendo bajar de nivel por bajo rendimiento")
                return 0.5  # Bajar nivel
            else:
                return prediccion
        else:
            # Regla heurística inicial
            return self._regla_heuristica_inicial(nivel)
    
    def _calcular_caracteristicas(self, nivel_actual: int) -> dict:
        """Calcula características basadas en historial reciente"""
        if len(self.historial_reciente) == 0:
            return {
                'nivel': nivel_actual,
                'tasa_aciertos': 0.7,
                'tiempo_promedio': 10.0,
                'ejercicios_consecutivos': 0,
                'fallos_consecutivos': self.fallos_consecutivos,
                'ejercicios_requeridos': float(self.ejercicios_requeridos)
            }
        
        # Calcular tasa de aciertos
        aciertos = sum(1 for e in self.historial_reciente if e['correcto'])
        tasa_aciertos = aciertos / len(self.historial_reciente)
        
        # Calcular tiempo promedio
        tiempo_prom = sum(e['tiempo'] for e in self.historial_reciente) / len(self.historial_reciente)
        
        # Calcular ejercicios consecutivos correctos
        consecutivos = 0
        for e in reversed(self.historial_reciente):
            if e['correcto']:
                consecutivos += 1
            else:
                break
        
        return {
            'nivel': nivel_actual,
            'tasa_aciertos': tasa_aciertos,
            'tiempo_promedio': tiempo_prom,
            'ejercicios_consecutivos': consecutivos,
            'fallos_consecutivos': self.fallos_consecutivos,
            'ejercicios_requeridos': float(self.ejercicios_requeridos)
        }
    
    def _calcular_dificultad_optima(self, correcto: bool, tiempo: float, nivel: int) -> float:
        """Determina la dificultad óptima basada en resultado actual"""
        # Reglas específicas para subir/bajar nivel
        ejercicios_consecutivos = sum(1 for e in self.historial_reciente if e['correcto'])
        
        # Para subir de nivel
        if nivel < 3 and ejercicios_consecutivos >= self.ejercicios_requeridos and correcto:
            print(f"Subiendo de nivel: ejercicios_consecutivos={ejercicios_consecutivos}, requeridos={self.ejercicios_requeridos}")
            return 2.0  # Valor más alto para asegurar subida de nivel
        # Para bajar de nivel    
        elif self.fallos_consecutivos >= self.ejercicios_requeridos and nivel > 1:
            print(f"Bajando de nivel: fallos_consecutivos={self.fallos_consecutivos}")
            return 0.5  # Valor más bajo para asegurar bajada de nivel
        # Mantener nivel pero ajustar dificultad
        elif correcto and tiempo < 8:
            return 1.1  # Aumentar dificultad ligeramente
        elif correcto and tiempo >= 8:
            return 1.0  # Mantener dificultad
        else:
            return 0.9  # Disminuir dificultad ligeramente
    
    def _entrenar_modelo(self):
        """Entrena el modelo de árbol de decisión"""
        self.model = DecisionTreeRegressor(
            max_depth=4,
            min_samples_split=5,
            min_samples_leaf=2
        )
        self.model.fit(self.features, self.targets)
    
    def _regla_heuristica_inicial(self, nivel: int) -> float:
        """Regla simple mientras se recolectan datos"""
        if self.fallos_consecutivos >= self.ejercicios_requeridos and nivel > 1:
            print("Regla heurística: Bajando de nivel por fallos consecutivos")
            return 0.5  # Bajar nivel
            
        ejercicios_consecutivos = sum(1 for e in self.historial_reciente if e['correcto'])
        if nivel < 3 and ejercicios_consecutivos >= self.ejercicios_requeridos:
            print("Regla heurística: Subiendo de nivel por ejercicios consecutivos correctos")
            return 2.0  # Subir nivel
            
        return 1.0  # Mantener nivel
        
    def reiniciar(self):
        """Reinicia el sistema de IA"""
        self.model = None
        self.features = pd.DataFrame(columns=[
            'nivel', 
            'tasa_aciertos', 
            'tiempo_promedio', 
            'ejercicios_consecutivos',
            'fallos_consecutivos',
            'ejercicios_requeridos'
        ])
        self.targets = pd.Series(name='dificultad_optima')
        self.historial_reciente.clear()
        self.fallos_consecutivos = 0
        self.mensaje_ayuda = ""

class GeneradorEjercicios:
    def __init__(self):
        self.ia = TrueAISystem()
        self.ultimo_ejercicio = None
        self.nivel_actual = 1
    
    def generar_ejercicio(self, nivel: int) -> Dict[str, int]:
        """Genera un ejercicio usando IA"""
        self.nivel_actual = nivel  # Actualizar nivel actual
        
        # Predecir dificultad óptima
        dificultad = self.ia.predecir_dificultad(nivel)
        
        # Generar números basados en dificultad
        num1, num2 = self._generar_numeros(dificultad)
        
        ejercicio = {
            'num1': num1,
            'num2': num2,
            'respuesta': num1 + num2,
            'dificultad': dificultad,
            'nivel': nivel,
            'timestamp': datetime.now().timestamp()
        }
        
        self.ultimo_ejercicio = ejercicio
        return ejercicio
    
    def registrar_resultado(self, correcto: bool, tiempo: float):
        """Registra el resultado para aprendizaje de IA"""
        if self.ultimo_ejercicio:
            nivel = self.ultimo_ejercicio.get('nivel', 1)  # Usar nivel 1 como valor predeterminado
            self.nivel_actual = nivel  # Actualizar el nivel actual
            self.ia.registrar_resultado(
                nivel,
                correcto,
                tiempo
            )
            
    @property
    def mensaje_ayuda(self) -> str:
        """Obtiene el mensaje de ayuda actual"""
        return self.ia.mensaje_ayuda
    
    def _generar_numeros(self, dificultad: float) -> tuple[int, int]:
        """Genera números basados en dificultad y nivel actual"""
        # Asegurarnos de que estamos en un nivel válido
        nivel_base = min(max(self.nivel_actual, 1), 3)
        
        if nivel_base == 1:  # Nivel 1
            return (
                random.randint(1, 10),
                random.randint(1, 10)
            )
        elif nivel_base == 2:  # Nivel 2
            return (
                random.randint(10, 50),
                random.randint(10, 50)
            )
        else:  # Nivel 3
            return (
                random.randint(50, 100),
                random.randint(50, 100)
            )
            
    def reiniciar(self):
        """Reinicia el generador de ejercicios"""
        self.ia.reiniciar()
        self.ultimo_ejercicio = None

# Instancia global del generador
generador = GeneradorEjercicios()

def generar_ejercicios_suma(nivel: int = 1) -> List[Dict[str, int]]:
    """Función de interfaz para generar ejercicios de suma"""
    return [generador.generar_ejercicio(nivel)] 