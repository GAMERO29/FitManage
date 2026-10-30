# Fragmento de código legado entregado en la Guía 1 (Ingeniería de Software II), Ejercicio 3.
# Sistema ficticio de facturación e inventario de una zapatería. Se conserva tal cual para auditarlo.
CONEXION_GLOBAL = None


def procesar_transaccion_venta(cliente_nombre, cliente_cedula, referencia_zapato, cantidad, metodo_pago):
    global CONEXION_GLOBAL
    cursor = CONEXION_GLOBAL.cursor()
    # Inyección SQL directa
    consulta = f"SELECT id, precio, stock FROM zapatos WHERE referencia = '{referencia_zapato}'"
    cursor.execute(consulta)
    zapato_id, precio, stock = cursor.fetchone()
    iva = 0.19  # IVA en duro
    total = (cantidad * precio) * (1 + iva)
    cursor.execute(f"""
    INSERT INTO ventas (cliente_nombre, cliente_cedula, zapato_id, cantidad, total_pagado)
    VALUES ('{cliente_nombre}', '{cliente_cedula}', {zapato_id}, {cantidad}, {total})
    """)
    if metodo_pago == "PAYU":
        api_key = "PROD_SECRET_KEY_EXPOSED_12345"  # Secreto expuesto
        print(f"Llamando a PayU con {api_key}...")
