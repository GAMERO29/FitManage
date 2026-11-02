"""RF-06 (CU-08): texto del recordatorio de pago que la recepcionista envía por WhatsApp."""

from datetime import date


def texto_recordatorio(nombres: str, vence: date, hoy: date) -> str:
    nombre = nombres.split()[0].capitalize()
    dias = (vence - hoy).days
    if dias < 0:
        raise ValueError("La membresía ya venció; no se envía recordatorio.")
    if dias == 0:
        return (
            f"Hola {nombre}, te recordamos que tu membresía en el gimnasio vence hoy. "
            "Te esperamos para renovarla."
        )
    if dias == 1:
        return (
            f"Hola {nombre}, te recordamos que tu membresía en el gimnasio vence mañana, "
            f"{vence.strftime('%d/%m/%Y')}. Te esperamos para renovarla."
        )
    return (
        f"Hola {nombre}, te recordamos que tu membresía en el gimnasio vence en {dias} días, "
        f"el {vence.strftime('%d/%m/%Y')}. Te esperamos para renovarla."
    )
