---
name: FitManage
description: Gestión de membresías y pagos para gimnasios MiPyme, con el anillo de vigencia como firma visual
colors:
  marca: "#23005A"
  marca-2: "#34106E"
  marca-3: "#5B3A99"
  lavanda: "#E2DAEF"
  lavanda-2: "#EFEAF7"
  lavanda-3: "#C9BCE0"
  fondo: "#F6F4FA"
  superficie: "#FFFFFF"
  tinta: "#1C1A26"
  tinta-2: "#4A4560"
  linea: "#DDD6EA"
  verde: "#1E8A4C"
  verde-logo: "#5EE08F"
  verde-fondo: "#E4F4EA"
  verde-tinta: "#0E4D2C"
  rojo: "#B42318"
  rojo-fondo: "#FBE9E7"
  rojo-tinta: "#7A1610"
  ambar: "#B45309"
  ambar-fondo: "#FCF0DE"
  ambar-tinta: "#6E3505"
  gris: "#77738A"
  gris-fondo: "#ECEAF1"
  gris-tinta: "#3D3A4D"
typography:
  display:
    fontFamily: "Sora, Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  estado:
    fontFamily: "Sora, sans-serif"
    fontSize: "52px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.035em"
  body:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  s: "10px"
  m: "14px"
  l: "20px"
  pill: "999px"
spacing:
  xs: "8px"
  s: "12px"
  m: "16px"
  l: "24px"
  xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.marca}"
    textColor: "{colors.superficie}"
    rounded: "{rounded.s}"
    height: "48px"
    padding: "0 22px"
  button-primary-hover:
    backgroundColor: "{colors.marca-2}"
  button-secondary:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.marca}"
    rounded: "{rounded.s}"
    height: "44px"
  nav-rail:
    backgroundColor: "{colors.marca}"
    textColor: "{colors.superficie}"
    width: "248px"
  sheet:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.m}"
    padding: "22px"
  result-active:
    backgroundColor: "{colors.verde-fondo}"
    textColor: "{colors.verde-tinta}"
    rounded: "{rounded.l}"
  result-expired:
    backgroundColor: "{colors.rojo-fondo}"
    textColor: "{colors.rojo-tinta}"
    rounded: "{rounded.l}"
---

## Overview

FitManage se ve como su logo: un anillo de vigencia que se gasta. La interfaz es de trabajo (modo Operate): riel morado a toda altura, superficies blancas sobre un fondo lavanda frío y el estado del socio dicho con palabras grandes y con un anillo que mide los días reales de la membresía.

## Colors

- El morado `marca` es el color del logo y ocupa el riel, los botones principales y los títulos.
- Verde para activo, ámbar para «vence en 3 días o menos», rojo solo para vencido o errores, gris para sin membresía. Los colores de estado nunca van solos: siempre hay palabra y forma.
- `verde-logo` solo se usa sobre morado (riel, login); sobre fondos claros se usa `verde`.

## Typography

- Sora (la letra del logotipo) para títulos, numerales y la palabra de estado.
- Atkinson Hyperlegible Next para la interfaz: distingue 0 de O y 1 de l, lo que importa al leer documentos.
- Ambas fuentes van incrustadas en el archivo para que funcionen sin internet.

## Layout

Riel de 248 px y contenido de hasta 1240 px. En recepción, la consulta ocupa la columna ancha y los vencimientos una columna de 320 px. Bajo 860 px el riel pasa a ser una barra superior con navegación desplazable.

## Elevation & Depth

Una sola sombra suave con desplazamiento (`0 1px 2px` + `0 6px 18px -8px` en morado translúcido) para las hojas. Los resultados de consulta no llevan sombra: los separa su color de estado.

## Shapes

Radios de 10 px (campos y botones), 14 px (hojas) y 20 px (resultado de consulta). Pastillas y chips completamente redondeados.

## Components

- **Anillo de vigencia**: círculo con pista translúcida y arco del color del estado; el arco es la parte de los días del plan que le quedan al socio. Vencido = pista roja vacía con los días de mora en el centro; sin membresía = pista punteada gris. En el pago, el anillo suma los días que ya tenía (verde) y los del plan nuevo (morado 3). Es el único elemento animado: el arco se dibuja al aparecer y se desactiva con `prefers-reduced-motion`.
- **Resultado de consulta**: anillo grande + palabra de estado en Sora 52 px + datos del socio + acción.
- **Opción de plan / chip de medio de pago**: botones con `aria-pressed`.

## Do's and Don'ts

- Usar el anillo solo donde mide días reales de una membresía o una proporción real.
- No usar etiquetas en mayúsculas sobre los títulos ni numerar secciones salvo los pasos del pago.
- No dejar huecos tipo «[precio]»: los datos de demostración van completos y marcados como ficticios.
