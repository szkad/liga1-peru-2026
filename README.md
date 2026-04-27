# 🏆 Liga 1 Perú 2026 — Dashboard de Estadísticas

Pipeline de datos completo que extrae información de **Transfermarkt**, la procesa con Python y la visualiza en **Power BI**.

---

## 📊 ¿Qué hace este proyecto?

| Etapa | Herramienta | Descripción |
|-------|-------------|-------------|
| Extracción | Python + BeautifulSoup | Lee HTML descargado de Transfermarkt |
| Transformación | Pandas | Limpia, estructura y relaciona los datos |
| Carga | CSV → Excel | Archivo maestro actualizable |
| Visualización | Power BI | Dashboard interactivo con KPIs y filtros |

---

## 🗂️ Estructura de datos (modelo estrella)

```
Dim_Jugadores.csv          → Catálogo de jugadores (valor, edad, posición, país)
Fixture_Liga1.csv          → Todos los partidos: fechas, resultados, jornadas
Fact_Resumen_Partidos.csv  → Minutos jugados por jugador por partido
Fact_Eventos_Detalle.csv   → Goles, asistencias, tarjetas y cambios por minuto
Fact_Info_Partido.csv      → Estadio, árbitro y entrenadores por partido
Fact_Estadisticas_Partido.csv → Tiros, corners, faltas y más por partido
```

---

## ⚙️ Cómo usarlo

### Requisitos
```bash
pip install pandas beautifulsoup4
```

### Flujo de trabajo

1. **Descarga los HTML** desde Transfermarkt:
   - Plantillas de equipo → guardar como `UNI.html`, `ALI.html`, etc.
   - Fixture de la temporada → guardar como `fixture.html`
   - Fichas de partido → guardar como `P26-J01-UNI-ALI.html`
   - Estadísticas de partido → guardar como `STATS-P26-J01-UNI-ALI.html`

2. **Ejecuta el script** (localmente o en Google Colab):
```bash
python liga1_peru.py
```

3. **Pega los CSV** en el Excel maestro y actualiza Power BI.

---

## 📁 Códigos de equipos

| Código | Equipo |
|--------|--------|
| UNI | Universitario |
| ALI | Alianza Lima |
| SCR | Sporting Cristal |
| MEL | FBC Melgar |
| CIE | Cienciano |
| ADT | AD Tarma |
| ATG | Atlético Grau |
| SBA | Sport Boys |
| SHU | Sport Huancayo |
| AAS | Alianza Atlético |
| COM | Comerciantes Unidos |
| CFC | Cusco FC |
| DGA | Deportivo Garcilaso |
| DMO | Deportivo Moquegua |
| FCA | FC Cajamarca |
| JPC | Juan Pablo II |
| LCH | Los Chankas |
| UTC | UTC |

---

## 🛠️ Stack técnico

- **Python 3.x** — lógica principal
- **BeautifulSoup4** — parsing de HTML
- **Pandas** — transformación y exportación de datos
- **Excel** — archivo maestro con historial acumulado
- **Power BI** — visualización final

---

## 👤 Autor

**Alexis Zapata** — Analista BI  
[linkedin.com/in/alexiszapata19](https://linkedin.com/in/alexiszapata19)
