from sqlalchemy import text
from sqlalchemy.orm import Session

from domain.entities import Venta, Zapato
from domain.ports import UnitOfWorkPort, VentaRepositoryPort, ZapatoRepositoryPort


class SqlAlchemyZapatoRepository(ZapatoRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def find_by_referencia(self, referencia: str) -> Zapato:
        row = self.session.execute(
            text("SELECT id, referencia, precio, stock FROM zapatos WHERE referencia = :ref"),
            {"ref": referencia},
        ).one()
        return Zapato(*row)


class SqlAlchemyVentaRepository(VentaRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, venta: Venta) -> None:
        self.session.execute(
            text("INSERT INTO ventas (cliente_nombre, cliente_cedula, zapato_id, cantidad, total_pagado) "
                 "VALUES (:n, :c, :z, :q, :t)"),
            {"n": venta.cliente_nombre, "c": venta.cliente_cedula, "z": venta.zapato_id,
             "q": venta.cantidad, "t": venta.total},
        )


class SqlAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session: Session):
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
