from application.dto import VentaRequestDTO, VentaResponseDTO
from domain.entities import Venta


class VentaMapper:
    @staticmethod
    def to_entity(dto: VentaRequestDTO, zapato_id: int, total) -> Venta:
        return Venta(dto.cliente_nombre, dto.cliente_cedula, zapato_id, dto.cantidad, total)

    @staticmethod
    def to_response(venta: Venta) -> VentaResponseDTO:
        return VentaResponseDTO(venta.zapato_id, venta.cantidad, venta.total)
