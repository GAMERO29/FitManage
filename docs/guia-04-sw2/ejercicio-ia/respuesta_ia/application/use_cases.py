from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from application.dto import VentaRequestDTO, VentaResponseDTO
from application.mappers import VentaMapper
from domain.ports import (
    LoggerPort,
    PaymentGatewayPort,
    TaxCalculatorPort,
    UnitOfWorkPort,
    VentaRepositoryPort,
    ZapatoRepositoryPort,
)


class ProcesarVentaUseCase:
    def __init__(self, zapatos: ZapatoRepositoryPort, ventas: VentaRepositoryPort,
                 pasarela: PaymentGatewayPort, impuestos: TaxCalculatorPort,
                 logger: LoggerPort, uow: UnitOfWorkPort):
        self.zapatos = zapatos
        self.ventas = ventas
        self.pasarela = pasarela
        self.impuestos = impuestos
        self.logger = logger
        self.uow = uow

    def execute(self, request: VentaRequestDTO) -> VentaResponseDTO:
        try:
            zapato = self.zapatos.find_by_referencia(request.referencia_zapato)
            subtotal = zapato.precio * request.cantidad
            total = subtotal + self.impuestos.calculate(subtotal)
            venta = VentaMapper.to_entity(request, zapato.id, total)
            self.ventas.save(venta)
            if request.metodo_pago == "PAYU":
                self.pasarela.charge(total)
            self.uow.commit()
            self.logger.info(f"Venta registrada por {total}")
            return VentaMapper.to_response(venta)
        except NoResultFound:
            self.uow.rollback()
            raise ValueError("Zapato no encontrado")
        except SQLAlchemyError:
            self.uow.rollback()
            raise
