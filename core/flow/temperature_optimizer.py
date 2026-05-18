"""
Optimizador de Temperatura Dinámica para Sibelium.
Calcula la temperatura óptima según el modelo, la cuantización y el propósito.
Basado en la Fórmula de Sibelium validada por IA Sabia.
"""

# Parámetros del modelo local
BITS_PER_WEIGHT = 4.5   # Llama 3.1 8B Q4_K_M
T_TARGET = 1.0           # Temperatura estándar ideal sin cuantizar

# Factor de especulación (gamma) según propósito cognitivo
GAMMA_TASK = {
    "reflexion": 0.1,
    "curiosidad": 0.3,
    "simulacion": 0.5,
    "prospeccion": 0.5,
    "consolidacion": 0.0,
}

# Rango de seguridad
T_MIN = 0.2
T_MAX = 0.8


def calcular_temperatura(proposito: str) -> float:
    """
    Calcula la temperatura óptima para un propósito cognitivo.
    
    Fórmula: T_sweet = T_target * (bits_per_weight / 16) * (1 + gamma_task)
    
    Args:
        proposito: Tipo de tarea ('reflexion', 'curiosidad', 'simulacion', 'prospeccion', 'consolidacion')
    
    Returns:
        Temperatura óptima acotada entre T_MIN y T_MAX
    """
    gamma = GAMMA_TASK.get(proposito, 0.2)
    t_sweet = T_TARGET * (BITS_PER_WEIGHT / 16.0) * (1.0 + gamma)
    return round(max(T_MIN, min(T_MAX, t_sweet)), 2)