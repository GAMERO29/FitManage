# Ejercicio 3 · Costo de distribuir FitManage

El cálculo se reproduce con `python docs/guia-05-sw2/costos.py`.

**Escenario:** los 4 contextos con lógica propia (Acceso, Socios, Membresías y cobros, Reportes) como funciones Lambda detrás de API Gateway, cada uno con su base PostgreSQL en RDS (*database per service*). Las Lambdas van dentro de una VPC para llegar a RDS, y salen a internet (WhatsApp, PayU) por un NAT Gateway. Se usan precios on-demand de us-east-1, sin créditos promocionales para cuentas nuevas, porque esos créditos se acaban.

| Concepto | USD/mes |
| --- | --- |
| RDS PostgreSQL db.t4g.micro × 4 (0,016 USD/h × 730 h) | 46,72 |
| Almacenamiento RDS, 20 GB × 4 (0,115 USD/GB-mes) | 9,20 |
| NAT Gateway (0,045 USD/h × 730 h) | 32,85 |
| NAT Gateway, 1 GB procesado (0,045 USD/GB) | 0,04 |
| IPv4 pública del NAT (0,005 USD/h × 730 h) | 3,65 |
| Secrets Manager, 4 secretos (0,40 USD c/u) | 1,60 |
| API Gateway HTTP, 18.000 peticiones (1,00 USD por millón) | 0,02 |
| Lambda (1 millón de peticiones y 400.000 GB-s gratis al mes) | 0,00 |
| **Total** | **94,08 (≈ COP 299.655 con TRM de 3.185,01)** |

**Comparación:** una MiPyme que vende 500 USD al mes y tiene un margen operativo del 20 % (supuesto del ejercicio) gana unos 100 USD. La arquitectura distribuida se llevaría el 18,8 % de las ventas y el 94 % del margen. El monolito del ADR N.° 03 cabe en la capa gratuita de un PaaS, a 0 USD, con las condiciones que ya advierte el DAD.

Lo que casi no cuesta es lo que se usa por petición (Lambda y API Gateway). Lo caro es lo que queda encendido todo el mes aunque nadie lo use: las cuatro bases de datos y el NAT Gateway.

## Fuentes

- RDS db.t4g.micro y almacenamiento: [AWS RDS Cost (2026)](https://selfhost-web.pages.dev/aws-rds-cost-breakdown-2026/) y [Bytebase, db.t4g.micro](https://www.bytebase.com/dbcost/rds/instance/db.t4g.micro.md).
- NAT Gateway, IPv4 pública y Secrets Manager: [AWS costs explained with real numbers](https://computingforgeeks.com/aws-costs-explained-real-numbers/).
- API Gateway HTTP: [Amazon API Gateway Pricing](https://cloudburn.io/blog/amazon-api-gateway-pricing).
- Capa gratuita de Lambda: [AWS Lambda cost breakdown for 2026](https://www.wiz.io/academy/cloud-cost/aws-lambda-cost-breakdown).
- TRM: [Portafolio, 23/10/2026](https://www.portafolio.co/economia/finanzas/precio-del-dolar-hoy-en-colombia-asi-cotiza-la-divisa-al-cierre-de-la-semana-504976).
