from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from application.use_cases import ProcesarVentaUseCase
from infrastructure.logger import PythonLogger
from infrastructure.payu_gateway import PayUGateway
from infrastructure.sqlalchemy_repositories import (
    SqlAlchemyUnitOfWork,
    SqlAlchemyVentaRepository,
    SqlAlchemyZapatoRepository,
)
from infrastructure.tax_calculator import ColombianTaxCalculator


def construir_caso_de_uso(url_base_de_datos: str) -> ProcesarVentaUseCase:
    session = Session(create_engine(url_base_de_datos))
    return ProcesarVentaUseCase(
        SqlAlchemyZapatoRepository(session),
        SqlAlchemyVentaRepository(session),
        PayUGateway(),
        ColombianTaxCalculator(),
        PythonLogger(),
        SqlAlchemyUnitOfWork(session),
    )
