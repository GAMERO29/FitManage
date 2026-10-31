"""La raíz de composición entrega los adaptadores reales; todo error del dominio tiene respuesta."""

from dominio.errores import ErrorDeDominio
from infraestructura.api import contenedor
from infraestructura.api.errores import respuesta_de_error
from infraestructura.correo import CorreoDjango
from infraestructura.reloj import RelojBogota


def test_en_produccion_el_reloj_es_el_de_bogota_y_el_correo_el_de_django():
    assert isinstance(contenedor.reloj(), RelojBogota)
    assert isinstance(contenedor.correo(), CorreoDjango)


def test_un_error_de_dominio_nuevo_sin_traduccion_cae_en_400():
    class ReglaNueva(ErrorDeDominio):
        pass

    respuesta = respuesta_de_error(ReglaNueva("algo no cuadra"))
    assert respuesta.status_code == 400
