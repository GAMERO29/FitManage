"""RF-06 (CU-08): texto del recordatorio de pago que la recepcionista envía por WhatsApp."""

from datetime import date

PLANTILLA = (
    "Hola {nombre}, te recordamos que tu membresía en el gimnasio vence {cuando}. "
    "Te esperamos para renovarla."
)


def texto_recordatorio(nombres: str, vence: date, hoy: date) -> str:
    return PLANTILLA.format(nombre=_primer_nombre(nombres), cuando=_cuando(vence, hoy))


def _primer_nombre(nombres: str) -> str:
    return nombres.split()[0].capitalize()


def _cuando(vence: date, hoy: date) -> str:
    dias = (vence - hoy).days
    fecha = vence.strftime("%d/%m/%Y")
    if dias < 0:
        raise ValueError("La membresía ya venció; no se envía recordatorio.")
    if dias == 0:
        return "hoy"
    if dias == 1:
        return f"mañana, {fecha}"
    return f"en {dias} días, el {fecha}"
