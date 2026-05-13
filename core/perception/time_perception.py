from datetime import datetime

WEEKDAYS = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"
]
MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


def get_moment_of_day(hour: int) -> str:
    if 5 <= hour < 12:
        return "mañana"
    if 12 <= hour < 18:
        return "tarde"
    if 18 <= hour < 22:
        return "noche"
    return "madrugada"


def get_season(month: int) -> str:
    if month in (12, 1, 2):
        return "invierno"
    if month in (3, 4, 5):
        return "primavera"
    if month in (6, 7, 8):
        return "verano"
    return "otoño"


def get_time_context(last_message_timestamp: str | None = None) -> str:
    now = datetime.now()
    weekday = WEEKDAYS[now.weekday()]
    month = MONTHS[now.month - 1]
    moment = get_moment_of_day(now.hour)
    season = get_season(now.month)
    text = (
        f"Es {weekday} {now.day} de {month} de {now.year}, {now.hour:02d}:{now.minute:02d} ({moment}). "
        f"Estación del año: {season}."
    )
    if last_message_timestamp:
        try:
            previous = datetime.fromisoformat(last_message_timestamp)
            diff = now - previous
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            text += f" Han pasado {diff.days * 24 + hours} horas y {minutes} minutos desde el último mensaje."
        except ValueError:
            text += " No se pudo calcular el tiempo desde el último mensaje."
    else:
        text += " No hay registro del último mensaje del usuario."
    return text