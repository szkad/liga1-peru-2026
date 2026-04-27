# -*- coding: utf-8 -*-
"""
Liga 1 Perú 2026 — Scraper de Transfermarkt
============================================
Genera 4 archivos CSV listos para Power BI:
  - Dim_Jugadores.csv
  - Fixture_Liga1.csv
  - Fact_Resumen_Partidos.csv
  - Fact_Eventos_Detalle.csv
  - Fact_Estadisticas_Partido.csv

Uso en Google Colab:
  1. Sube los HTML a la sesión
  2. Ejecuta las celdas en orden
  3. Descarga los CSV generados
"""

# ============================================================
# IMPORTS (una sola vez)
# ============================================================
import pandas as pd
from bs4 import BeautifulSoup
import glob
import os
import re

print("✅ Librerías cargadas correctamente.")


# ============================================================
# CONSTANTES GLOBALES
# ============================================================

# Códigos de los 18 equipos de la Liga 1 2026
EQUIPOS = [
    'UNI', 'ALI', 'SCR', 'MEL', 'ADT', 'CIE', 'SBA',
    'AAS', 'ATG', 'COM', 'CFC', 'DGA', 'DMO', 'FCA', 'JPC', 'LCH', 'SHU', 'UTC'
]

# Diccionario nombre web → código 3 letras (único en todo el proyecto)
MAPA_EQUIPOS = {
    "Universitario":              "UNI",
    "Alianza Lima":               "ALI",
    "Sporting Cristal":           "SCR",
    "Sport. Cristal":             "SCR",
    "FBC Melgar":                 "MEL",
    "Cienciano":                  "CIE",
    "Cusco FC":                   "CFC",
    "Dep. Garcilaso":             "DGA",
    "Deportivo Garcilaso":        "DGA",
    "Sport Boys":                 "SBA",
    "Sport Huancayo":             "SHU",
    "UTC":                        "UTC",
    "Universidad Técnica de Cajamarca": "UTC",
    "Alianza Atl.":               "AAS",
    "Alianza Atlético":           "AAS",
    "AD Tarma":                   "ADT",
    "Asociación Deportiva Tarma": "ADT",
    "Atlético Grau":              "ATG",
    "Carlos A. Mannucci":         "MAN",
    "Los Chankas":                "LCH",
    "Comerciantes":               "COM",
    "Comerciantes Unidos":        "COM",
    "Juan Pablo II":              "JPC",
    "FC Cajamarca":               "FCA",
    "Dep. Moquegua":              "DMO",
    "Deportivo Moquegua":         "DMO",
}


# ============================================================
# FUNCIONES UTILITARIAS COMPARTIDAS
# ============================================================

def extraer_id_tm(link):
    """Extrae el ID numérico de Transfermarkt desde un href de jugador."""
    if not link:
        return "0"
    match = re.search(r'/spieler/(\d+)', link)
    return match.group(1) if match else "0"


def extraer_id_generico(href, tipo):
    """Extrae el ID numérico de entrenador o árbitro desde un href."""
    if not href:
        return "0"
    match = re.search(rf'/{tipo}/(\d+)', href)
    return match.group(1) if match else "0"


def limpiar_nombre_desde_url(href):
    """Convierte slug de URL en nombre legible (ej: 'john-doe' → 'John Doe')."""
    if not href:
        return "Desconocido"
    try:
        slug = href.strip('/').split('/')[0]
        return slug.replace('-', ' ').title()
    except Exception:
        return "Desconocido"


def codigo_equipo(nombre_web):
    """Devuelve el código de 3 letras para un equipo dado su nombre en la web."""
    return MAPA_EQUIPOS.get(nombre_web, nombre_web[:3].upper())


def decodificar_minuto_sprite(tag):
    """
    Intenta leer el minuto de un evento desde:
      1. Texto visible del span ("45'", "90+3'")
      2. CSS background-position (sprites de Transfermarkt)
    """
    if not tag:
        return 0

    texto = tag.get_text(strip=True).replace("'", "").replace("+", "")
    if texto and texto.isdigit():
        val = int(texto)
        return 90 + val if val < 15 else val

    style = tag.get('style', '')
    match = re.search(r'background-position:\s*(-?\d+)px\s*(-?\d+)px', style)
    if match:
        x = abs(int(match.group(1)))
        y = abs(int(match.group(2)))
        decena = int(y / 36)
        unidad = int(x / 36) + 1
        return (decena * 10) + unidad

    return 0


def identificar_equipo_evento(item_html):
    """Identifica el equipo de un evento buscando el escudo dentro del HTML."""
    div_wappen = item_html.find('div', class_='sb-aktion-wappen')
    if div_wappen:
        img = div_wappen.find('img')
        if img:
            nombre_equipo = img.get('title', '').strip()
            for nombre, codigo in MAPA_EQUIPOS.items():
                if nombre in nombre_equipo:
                    return codigo
    return "DESCONOCIDO"


def exportar_csv(df, nombre_archivo, descripcion):
    """Exporta un DataFrame a CSV y muestra un resumen."""
    df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
    print(f"✅ {descripcion}: {len(df)} registros → '{nombre_archivo}'")


# ============================================================
# SECCIÓN 1 — PLANTILLAS (Dim_Jugadores)
# ============================================================

def procesar_plantilla(codigo):
    """
    Lee el HTML de un equipo y extrae los datos de sus jugadores.
    Retorna un DataFrame o None si el archivo no existe / no tiene datos.
    """
    nombre_archivo = f"{codigo}.html"

    if not os.path.exists(nombre_archivo):
        print(f"  ⚠️  Falta archivo: {nombre_archivo} (saltando...)")
        return None

    print(f"  🔨 Procesando: {nombre_archivo}")

    with open(nombre_archivo, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    tabla = soup.find('table', class_='items')
    if not tabla:
        print(f"  ❌ No se encontró tabla de jugadores en {nombre_archivo}")
        return None

    filas = tabla.find_all('tr', class_=['odd', 'even'])
    datos = []

    for fila in filas:
        try:
            tabla_inline = fila.find('table', class_='inline-table')
            if not tabla_inline:
                continue

            # Nombre e ID del jugador
            img_tag = tabla_inline.find('img')
            nombre = img_tag['title'] if img_tag else "Desconocido"
            url_foto = img_tag.get('data-src') or img_tag.get('src') or ""

            td_hauptlink = tabla_inline.find('td', class_='hauptlink')
            link_perfil = td_hauptlink.find('a') if td_hauptlink else None
            id_tm = extraer_id_tm(link_perfil.get('href', '') if link_perfil else '')

            tds_inline = tabla_inline.find_all('td')
            posicion = tds_inline[-1].get_text(strip=True) if tds_inline else "Desconocido"

            # Celdas principales de la fila
            celdas = fila.find_all('td', recursive=False)

            dorsal = celdas[0].get_text(strip=True).replace('-', '0') or "0"

            nac_raw = celdas[2].get_text(strip=True)
            fecha_nac = nac_raw.split('(')[0].strip() if '(' in nac_raw else nac_raw
            match_edad = re.search(r'\((\d+)\)', nac_raw)
            edad = int(match_edad.group(1)) if match_edad else 0

            imgs_pais = celdas[3].find_all('img', class_='flaggenrahmen')
            nacionalidad = " / ".join([img['title'] for img in imgs_pais]) if imgs_pais else "Desconocido"

            pie      = celdas[5].get_text(strip=True)
            fichado  = celdas[6].get_text(strip=True)
            contrato = celdas[8].get_text(strip=True)

            # Valor de mercado
            valor_raw = celdas[9].get_text(strip=True)
            valor = 0.0
            if 'mill' in valor_raw:
                valor = float(valor_raw.replace(' mill. €', '').replace(',', '.')) * 1_000_000
            elif 'mil' in valor_raw:
                valor = float(valor_raw.replace(' mil €', '').replace(',', '.')) * 1_000

            datos.append({
                'ID_Equipo':        codigo,
                'ID_Jugador':       id_tm,
                'Dorsal':           dorsal,
                'Jugador':          nombre,
                'Posicion':         posicion,
                'Fecha_Nacimiento': fecha_nac,
                'Edad':             edad,
                'Pais':             nacionalidad,
                'Pie':              pie,
                'Fichado':          fichado,
                'Contrato':         contrato,
                'Valor_EUR':        valor,
                'URL_Foto':         url_foto,
            })

        except Exception as e:
            print(f"    ⚠️  Fila omitida en {nombre_archivo}: {e}")
            continue

    return pd.DataFrame(datos) if datos else None


def generar_dim_jugadores():
    print("\n🚀 SECCIÓN 1 — Generando Dim_Jugadores...\n")
    tablas = []

    for codigo in EQUIPOS:
        df = procesar_plantilla(codigo)
        if df is not None and not df.empty:
            tablas.append(df)

    if not tablas:
        print("⚠️  No se generaron datos. Verifica que los HTML estén subidos.")
        return

    df_final = pd.concat(tablas, ignore_index=True)
    df_final = df_final.drop_duplicates(subset=['ID_Jugador'], keep='first')
    exportar_csv(df_final, 'Dim_Jugadores.csv', 'Dim_Jugadores')
    print(df_final[['ID_Equipo', 'Jugador', 'Edad', 'Valor_EUR']].head())


# ============================================================
# SECCIÓN 2 — FIXTURE
# ============================================================

def generar_fixture():
    print("\n🚀 SECCIÓN 2 — Generando Fixture...\n")

    archivo = 'fixture.html'
    if not os.path.exists(archivo):
        print("⚠️  Sube el archivo 'fixture.html' y vuelve a ejecutar.")
        return

    with open(archivo, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    lista_partidos = []
    jornada_actual = "00"
    ultima_fecha = "Por definir"

    for tabla in soup.find_all('table'):
        # Detectar número de jornada
        try:
            box = tabla.find_previous('div', class_='content-box-headline')
            if box:
                texto = box.get_text().strip()
                if "JORNADA" in texto.upper():
                    num = ''.join(filter(str.isdigit, texto.split('.')[0]))
                    jornada_actual = num.zfill(2)
        except Exception:
            pass

        for fila in tabla.find_all('tr'):
            try:
                links_equipos = [
                    e.get_text().strip()
                    for e in fila.find_all('a', title=True)
                    if 'verein' in e.get('href', '') and e.get_text().strip()
                ]
                if len(links_equipos) < 2:
                    continue

                nom_local, nom_visita = links_equipos[0], links_equipos[1]
                id_local   = codigo_equipo(nom_local)
                id_visita  = codigo_equipo(nom_visita)

                # Resultado
                goles_local, goles_visita = 0, 0
                estado = "Programado"
                link_res = fila.find('a', title=lambda t: t and ('Ficha' in t or 'Informe' in t))
                if link_res:
                    res = link_res.get_text().strip()
                    if ":" in res and res != "-:-":
                        partes = res.split(':')
                        goles_local   = int(partes[0])
                        goles_visita  = int(partes[1])
                        estado = "Finalizado"

                # Fecha con memoria (hereda la última válida si la celda está vacía)
                celdas = fila.find_all('td')
                if celdas:
                    txt_raw = celdas[0].get_text().strip()
                    if len(txt_raw) > 5:
                        match_f = re.search(r'\d{2}/\d{2}/\d{2,4}', txt_raw)
                        if match_f:
                            ultima_fecha = match_f.group(0)
                            if len(ultima_fecha) == 8:  # dd/mm/yy → dd/mm/yyyy
                                ultima_fecha = ultima_fecha[:-2] + "20" + ultima_fecha[-2:]

                lista_partidos.append({
                    'ID_Partido':    f"P26-J{jornada_actual}-{id_local}-{id_visita}",
                    'Jornada':       jornada_actual,
                    'Fecha':         ultima_fecha,
                    'ID_Local':      id_local,
                    'ID_Visitante':  id_visita,
                    'Equipo_Local':  nom_local,
                    'Equipo_Visita': nom_visita,
                    'Goles_Local':   goles_local,
                    'Goles_Visita':  goles_visita,
                    'Estado':        estado,
                })

            except Exception as e:
                print(f"  ⚠️  Fila de fixture omitida: {e}")
                continue

    if not lista_partidos:
        print("⚠️  No se extrajeron partidos del fixture.")
        return

    df = pd.DataFrame(lista_partidos).drop_duplicates(subset=['ID_Partido'])
    exportar_csv(df, 'Fixture_Liga1.csv', 'Fixture')
    pd.set_option('display.max_colwidth', None)
    print(df[['ID_Partido', 'Fecha', 'ID_Local', 'ID_Visitante']].head(10))


# ============================================================
# SECCIÓN 3 — INFORMACIÓN DE PARTIDOS
#             (Fact_Resumen_Partidos + Fact_Eventos_Detalle)
# ============================================================

def procesar_partido(archivo, tabla_resumen, tabla_eventos):
    """Extrae eventos y alineaciones de la ficha HTML de un partido."""
    id_partido = os.path.basename(archivo).replace('.html', '')

    with open(archivo, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    info_jugador = {}  # {id_tm: {Min_Entra, Min_Sale}}

    def registrar_evento(id_equipo, id_jug, minuto, tipo, detalle):
        tabla_eventos.append({
            'ID_Partido':    id_partido,
            'ID_Equipo':     id_equipo,
            'ID_Jugador_TM': id_jug,
            'Minuto':        minuto,
            'Tipo_Evento':   tipo,
            'Detalle':       detalle,
        })

    # --- A. GOLES ---
    caja_goles = soup.find('div', id='sb-tore')
    if caja_goles:
        for item in caja_goles.find_all('li'):
            try:
                id_equipo = identificar_equipo_evento(item)
                div_accion = item.find('div', class_='sb-aktion-aktion')
                if not div_accion:
                    continue
                links = div_accion.find_all('a', class_='wichtig')
                if not links:
                    continue

                id_gol = extraer_id_tm(links[0]['href'])
                minuto = decodificar_minuto_sprite(item.find('span', class_='sb-sprite-uhr-klein'))
                if minuto == 0:
                    m = re.search(r"(\d+)'", item.get_text())
                    if m: minuto = int(m.group(1))

                texto = div_accion.get_text()
                tipo_gol = texto.split(',')[1].strip() if ',' in texto else "Jugada"
                registrar_evento(id_equipo, id_gol, minuto, "Gol", tipo_gol)

                if len(links) > 1:
                    id_asist = extraer_id_tm(links[1]['href'])
                    registrar_evento(id_equipo, id_asist, minuto, "Asistencia", f"Pase para {tipo_gol}")
            except Exception as e:
                print(f"  ⚠️  Gol omitido en {id_partido}: {e}")

    # --- B. TARJETAS ---
    caja_tarjetas = soup.find('div', id='sb-karten')
    if caja_tarjetas:
        for item in caja_tarjetas.find_all('li'):
            try:
                id_equipo = identificar_equipo_evento(item)
                div_foto = item.find('div', class_='sb-aktion-spielerbild')
                link = div_foto.find('a') if div_foto else None
                if not link:
                    continue

                id_jug = extraer_id_tm(link['href'])
                clases = item.find('span', class_='sb-sprite').get('class', []) if item.find('span', class_='sb-sprite') else []
                tipo = "Roja" if 'sb-rot' in clases else ("Doble Amarilla" if 'sb-gelb-rot' in clases else "Amarilla")

                div_accion = item.find('div', class_='sb-aktion-aktion')
                razon = div_accion.get_text().split(',')[-1].strip() if div_accion and ',' in div_accion.get_text() else "Falta"

                minuto = decodificar_minuto_sprite(item.find('span', class_='sb-sprite-uhr-klein'))
                registrar_evento(id_equipo, id_jug, minuto, f"Tarjeta {tipo}", razon)
            except Exception as e:
                print(f"  ⚠️  Tarjeta omitida en {id_partido}: {e}")

    # --- C. CAMBIOS ---
    caja_cambios = soup.find('div', id='sb-wechsel')
    if caja_cambios:
        for item in caja_cambios.find_all('li'):
            try:
                id_equipo = identificar_equipo_evento(item)
                minuto = decodificar_minuto_sprite(
                    item.find('div', class_='sb-aktion-uhr').find('span', class_='sb-sprite-uhr-klein')
                    if item.find('div', class_='sb-aktion-uhr') else None
                )
                if minuto == 0:
                    m = re.search(r"(\d+)'", item.get_text())
                    minuto = int(m.group(1)) if m else 45

                span_entra = item.find('span', class_='sb-aktion-wechsel-ein')
                if span_entra:
                    link = span_entra.find('a')
                    if link:
                        id_in = extraer_id_tm(link['href'])
                        registrar_evento(id_equipo, id_in, minuto, "Cambio In", "Entra al campo")
                        info_jugador.setdefault(id_in, {})['Min_Entra'] = minuto

                span_sale = item.find('span', class_='sb-aktion-wechsel-aus')
                if span_sale:
                    link = span_sale.find('a')
                    if link:
                        id_out = extraer_id_tm(link['href'])
                        motivo = "Lesión" if "Lesión" in span_sale.get_text() else "Táctica"
                        registrar_evento(id_equipo, id_out, minuto, "Cambio Out", f"Sale por {motivo}")
                        info_jugador.setdefault(id_out, {})['Min_Sale'] = minuto
            except Exception as e:
                print(f"  ⚠️  Cambio omitido en {id_partido}: {e}")

    # --- D. ALINEACIONES / MINUTOS JUGADOS ---
    for header in soup.find_all('div', class_='aufstellung-unterueberschrift-mannschaft'):
        nombre_equipo_web = header.get_text().strip()
        id_equipo = next(
            (codigo for nombre, codigo in MAPA_EQUIPOS.items() if nombre in nombre_equipo_web),
            "DESCONOCIDO"
        )
        if id_equipo == "DESCONOCIDO":
            continue

        padre = header.parent

        def procesar_jugador(obj_html, es_titular):
            try:
                if "Entrenador" in obj_html.get_text():
                    return
                elem_nombre = obj_html.find('span', class_='formation-number-name') if es_titular else obj_html
                elem_dorsal = obj_html.find('div', class_='tm-shirt-number')
                link_tag = elem_nombre.find('a') if elem_nombre else None
                if not link_tag:
                    return

                nombre  = limpiar_nombre_desde_url(link_tag['href'])
                id_tm   = extraer_id_tm(link_tag['href'])
                dorsal  = elem_dorsal.get_text().strip() if elem_dorsal else "0"
                tiempos = info_jugador.get(id_tm, {})

                if es_titular:
                    minutos = tiempos.get('Min_Sale', 90)
                else:
                    entra = tiempos.get('Min_Entra', 0)
                    minutos = 90 - entra if entra > 0 else 0

                tabla_resumen.append({
                    'ID_Partido':    id_partido,
                    'ID_Equipo':     id_equipo,
                    'ID_Jugador_TM': id_tm,
                    'Jugador':       nombre,
                    'Dorsal':        dorsal,
                    'Condicion':     "Titular" if es_titular else "Suplente",
                    'Min_Jugados':   minutos,
                })
            except Exception as e:
                print(f"  ⚠️  Jugador omitido en {id_partido}: {e}")

        for contenedor in padre.find_all('div', class_='formation-player-container'):
            procesar_jugador(contenedor, True)

        tablas_banco = padre.find_all('table', class_='ersatzbank')
        if not tablas_banco:
            for h in padre.find_next_siblings('div', class_='aufstellung-ersatzbank-box', limit=1):
                tb = h.find('table', class_='ersatzbank')
                if tb: tablas_banco.append(tb)

        for tb in tablas_banco:
            for fila in tb.find_all('tr'):
                procesar_jugador(fila, False)


def generar_info_partidos():
    print("\n🚀 SECCIÓN 3 — Generando Fact_Resumen y Fact_Eventos...\n")

    archivos = sorted(glob.glob("P26-*.html"))
    if not archivos:
        print("⚠️  No se encontraron archivos de partido (P26-*.html).")
        return

    tabla_resumen = []
    tabla_eventos = []

    for f in archivos:
        print(f"  🔨 Procesando: {f}")
        procesar_partido(f, tabla_resumen, tabla_eventos)

    if tabla_resumen:
        df_resumen = pd.DataFrame(tabla_resumen).drop_duplicates(subset=['ID_Partido', 'ID_Jugador_TM'])
        exportar_csv(df_resumen, 'Fact_Resumen_Partidos.csv', 'Fact_Resumen_Partidos')

    if tabla_eventos:
        df_eventos = pd.DataFrame(tabla_eventos)
        exportar_csv(df_eventos, 'Fact_Eventos_Detalle.csv', 'Fact_Eventos_Detalle')
        print(df_eventos[['ID_Equipo', 'Tipo_Evento', 'Detalle']].head())
    else:
        print("⚠️  No se encontraron eventos en los archivos procesados.")


# ============================================================
# SECCIÓN 4 — INFORMACIÓN TÉCNICA DEL PARTIDO
#             (Estadio, Árbitro, DT Local, DT Visita)
# ============================================================

def procesar_info_tecnica(archivo):
    id_partido = os.path.basename(archivo).replace('.html', '')

    with open(archivo, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    estadio, arbitro, id_arbitro = "Desconocido", "Desconocido", "0"

    p_info = soup.find('p', class_='sb-zusatzinfos')
    if p_info:
        span_estadio = p_info.find('span', class_='hide-for-small')
        if span_estadio:
            link = span_estadio.find('a')
            if link: estadio = link.get_text().strip()

        link_arbitro = p_info.find('a', href=re.compile(r'/schiedsrichter/'))
        if link_arbitro:
            arbitro    = link_arbitro.get('title') or link_arbitro.get_text()
            id_arbitro = extraer_id_generico(link_arbitro['href'], 'schiedsrichter')

    def buscar_dt(tabla):
        if not tabla:
            return "Desconocido", "0"
        for fila in tabla.find_all('tr', class_='bench-table__tr'):
            if "Entrenador" in fila.get_text():
                link = fila.find('a')
                if link:
                    return (link.get('title') or link.get_text()), extraer_id_generico(link['href'], 'trainer')
                return fila.get_text().replace("Entrenador:", "").strip(), "0"
        return "Desconocido", "0"

    tablas_banco = soup.find_all('table', class_='ersatzbank')
    dt_local,  id_dt_local  = buscar_dt(tablas_banco[0] if len(tablas_banco) >= 1 else None)
    dt_visita, id_dt_visita = buscar_dt(tablas_banco[1] if len(tablas_banco) >= 2 else None)

    return {
        'ID_Partido':   id_partido,
        'Estadio':      estadio,
        'ID_Arbitro':   id_arbitro,
        'Arbitro':      arbitro,
        'ID_DT_Local':  id_dt_local,
        'DT_Local':     dt_local,
        'ID_DT_Visita': id_dt_visita,
        'DT_Visita':    dt_visita,
    }


def generar_info_tecnica():
    print("\n🚀 SECCIÓN 4 — Generando Info Técnica de Partidos...\n")

    archivos = sorted(glob.glob("P26-*.html"))
    if not archivos:
        print("⚠️  No se encontraron archivos de partido (P26-*.html).")
        return

    lista = []
    for f in archivos:
        try:
            lista.append(procesar_info_tecnica(f))
            print(f"  🔨 Procesado: {f}")
        except Exception as e:
            print(f"  ⚠️  Error en {f}: {e}")

    if lista:
        df = pd.DataFrame(lista)
        exportar_csv(df, 'Fact_Info_Partido.csv', 'Fact_Info_Partido')
        print(df[['ID_Partido', 'Arbitro', 'DT_Local', 'DT_Visita']].head())


# ============================================================
# SECCIÓN 5 — ESTADÍSTICAS DE PARTIDO (STATS-*.html)
# ============================================================

def procesar_stats(archivo):
    id_partido = os.path.basename(archivo).replace('STATS-', '').replace('.html', '')

    with open(archivo, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    datos = {'ID_Partido': id_partido}

    for titulo_div in soup.find_all('div', class_='unterueberschrift'):
        label = titulo_div.get_text().strip()

        # Posesión da datos basura en TM → la saltamos
        if any(p in label for p in ["Posesión", "Ballbesitz"]):
            continue

        caja = titulo_div.find_next_sibling('div', class_='sb-statistik')
        if not caja:
            continue

        valores = caja.find_all('div', class_='sb-statistik-zahl')
        if len(valores) < 2:
            continue

        # Nombre de columna limpio (sin tildes, sin espacios)
        col = (label
               .replace(' ', '_')
               .replace('ó', 'o').replace('é', 'e')
               .replace('á', 'a').replace('í', 'i')
               .replace('ú', 'u').replace('.', ''))

        datos[f"{col}_Local"]  = valores[0].get_text(strip=True)
        datos[f"{col}_Visita"] = valores[1].get_text(strip=True)

    return datos


def generar_estadisticas():
    print("\n🚀 SECCIÓN 5 — Generando Estadísticas de Partido...\n")

    archivos = sorted(glob.glob("STATS-*.html"))
    if not archivos:
        print("⚠️  No se encontraron archivos de estadísticas (STATS-*.html).")
        return

    lista = []
    for f in archivos:
        try:
            lista.append(procesar_stats(f))
            print(f"  🔨 Procesado: {f}")
        except Exception as e:
            print(f"  ⚠️  Error en {f}: {e}")

    if lista:
        df = pd.DataFrame(lista).fillna(0)
        exportar_csv(df, 'Fact_Estadisticas_Partido.csv', 'Fact_Estadisticas_Partido')
        print(df.head())


# ============================================================
# PUNTO DE ENTRADA — Ejecuta todas las secciones en orden
# ============================================================

if __name__ == "__main__":
    generar_dim_jugadores()
    generar_fixture()
    generar_info_partidos()
    generar_info_tecnica()
    generar_estadisticas()
    print("\n🏆 ¡Pipeline completo! Todos los CSV generados.")
