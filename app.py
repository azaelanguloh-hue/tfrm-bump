import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(
    page_title="BUMP — Panel Diario",
    layout="centered",
    page_icon="💧"
)

# -----------------------------
# Estilos (limpio y amigable)
# -----------------------------
st.markdown("""
<style>
.big-card {
    padding: 18px;
    border-radius: 16px;
    border: 1px solid rgba(0,0,0,0.08);
    background: rgba(255,255,255,0.70);
}
.kpi {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
}
.kpi-sub {
    font-size: 0.95rem;
    opacity: 0.82;
}
.small-note {
    font-size: 0.95rem;
    opacity: 0.82;
}
hr { margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Reglas (las mismas que ya definimos)
# -----------------------------
def nivel_por_dias(dias: int) -> str:
    if dias == 0:
        return "Sedentaria"
    if 1 <= dias <= 3:
        return "Ligera"
    if 4 <= dias <= 5:
        return "Moderada"
    return "Intensa"  # 6-7

def factor_proteina_por_nivel(nivel: str) -> float:
    # Todas arriba de 1.2 (como pediste)
    if nivel in ["Sedentaria", "Ligera"]:
        return 1.3
    if nivel == "Moderada":
        return 1.5
    return 1.7  # Intensa

def meta_dias_recomendada(dias: int):
    """
    Recomendación clara:
    - Base mínima: 3 días/sem
    - Ideal: 4–5 días/sem
    - Si ya hace 6–7: mantener y priorizar recuperación
    """
    if dias == 0:
        return ("Meta mínima", 3, "Empieza con 3 días/semana (20–30 min) suave.")
    if 1 <= dias <= 2:
        return ("Meta mínima", 3, "Súbele a 3 días/semana para crear consistencia.")
    if dias == 3:
        return ("Meta ideal", 4, "Vas bien. Si puedes, sube a 4 días/semana.")
    if dias == 4:
        return ("Meta ideal", 5, "Excelente. Si te sientes bien, apunta a 5 días/semana.")
    if dias == 5:
        return ("Mantén", 5, "Perfecto. Mantén 5 días/semana.")
    return ("Alto nivel", 6, "Muy bien. Prioriza descanso, sueño y 1 día suave.")

def build_ics(title: str, start_dt: datetime, duration_min: int, count: int, interval_hours: int):
    """
    Crea un .ics con eventos repetidos (count eventos)
    """
    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%S")

    # ICS básico (sin timezone explícito para que el calendario lo ajuste local)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TFRM//BUMP//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    uid_base = f"{int(datetime.now().timestamp())}@tfrm-bump"

    for i in range(count):
        s = start_dt + timedelta(hours=i * interval_hours)
        e = s + timedelta(minutes=duration_min)
        uid = f"{uid_base}-{i}"

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{fmt(datetime.now())}",
            f"DTSTART:{fmt(s)}",
            f"DTEND:{fmt(e)}",
            f"SUMMARY:{title}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\n".join(lines).encode("utf-8")

# -----------------------------
# UI
# -----------------------------
st.title("BUMP — Panel Diario")
st.caption("Agua • Proteína • Actividad (simple, claro y para usar diario)")

tab1, tab2 = st.tabs(["📌 Mi Panel", "⏰ Recordatorios"])

# -----------------------------
# TAB 1 — Mi Panel
# -----------------------------
with tab1:
    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.subheader("Tus datos")

    peso_kg = st.number_input("Tu peso (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.1)
    dias_ejercicio = st.slider("¿Cuántos días a la semana haces actividad física?", 0, 7, 3)

    agua_op = st.radio(
        "Agua por kg (elige 1 opción)",
        options=["30 ml por kg (normal)", "35 ml por kg (calor / sudas más)"],
        index=1,
        horizontal=True
    )

    st.markdown('<p class="small-note">Tip: si vives en clima caluroso (Q. Roo/Yucatán), casi siempre 35 ml/kg.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Cálculos
    ml_por_kg = 30 if "30 ml" in agua_op else 35
    agua_ml = peso_kg * ml_por_kg
    agua_l = agua_ml / 1000

    nivel = nivel_por_dias(dias_ejercicio)
    prot_factor = factor_proteina_por_nivel(nivel)
    proteina_g = peso_kg * prot_factor

    meta_tipo, meta_dias, meta_texto = meta_dias_recomendada(dias_ejercicio)

    st.markdown("---")
    st.subheader("Tus números del día")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="big-card">', unsafe_allow_html=True)
        st.markdown("💧 **Agua recomendada**")
        st.markdown(f'<div class="kpi">{agua_l:.2f} L</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-sub">({agua_ml:,.0f} ml/día • {ml_por_kg} ml/kg)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="big-card">', unsafe_allow_html=True)
        st.markdown("🍗 **Proteína recomendada**")
        st.markdown(f'<div class="kpi">{proteina_g:,.0f} g</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-sub">({prot_factor} g/kg según tu actividad)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.markdown("🏃‍♀️ **Actividad física**")
    st.write(f"**Tu nivel actual:** {nivel} (por {dias_ejercicio} días/semana)")
    st.write(f"**{meta_tipo}:** {meta_dias} días/semana")
    st.write(f"**Sugerencia:** {meta_texto}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Educativo y de apoyo. Si estás embarazada/lactando o con condiciones médicas, consulta a un profesional.")

# -----------------------------
# TAB 2 — Recordatorios
# -----------------------------
with tab2:
    st.subheader("Recordatorios de agua")
    st.caption("Aquí puedes llevar checklist y generar horarios sugeridos (descargables).")

    # Reutilizar inputs (si el usuario aún no fue a Tab 1)
    # Tomamos valores con defaults si no existen en sesión
    peso_kg_2 = st.session_state.get("peso_kg", None)
    # Streamlit no guarda automáticamente las variables; entonces recalculamos con inputs sencillos aquí:
    colA, colB = st.columns(2)

    with colA:
        peso_r = st.number_input("Tu peso (kg) (para recordatorios)", min_value=30.0, max_value=250.0, value=70.0, step=0.1, key="peso_recordatorios")
        agua_factor = st.radio("Factor de agua", ["30 ml/kg", "35 ml/kg"], index=1, horizontal=True, key="agua_factor_recordatorios")

    with colB:
        presentacion = st.selectbox("¿Cómo la prefieres medir?", ["Vasos de 250 ml", "Botellas de 500 ml", "Litros"], index=1)
        horas_despierta = st.slider("Horas despierta al día (aprox.)", 10, 18, 14)

    mlkg = 30 if agua_factor == "30 ml/kg" else 35
    agua_ml_r = peso_r * mlkg
    agua_l_r = agua_ml_r / 1000

    # Convertir a "unidades" para checklist
    if presentacion == "Vasos de 250 ml":
        unidad_ml = 250
        unidades = int(round(agua_ml_r / unidad_ml))
        unidad_txt = "vasos"
    elif presentacion == "Botellas de 500 ml":
        unidad_ml = 500
        unidades = int(round(agua_ml_r / unidad_ml))
        unidad_txt = "botellas"
    else:
        unidades = int(round(agua_l_r))
        unidad_txt = "litros"
        unidad_ml = None

    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.markdown("✅ **Meta de agua de hoy**")
    st.markdown(f'<div class="kpi">{agua_l_r:.2f} L</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-sub">{agua_ml_r:,.0f} ml/día • {mlkg} ml/kg</div>', unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-sub'>Equivale aprox. a <b>{unidades} {unidad_txt}</b>.</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Checklist rápido")

    # Checklist: 12 slots máximo para no saturar
    max_slots = min(max(unidades, 1), 12) if unidad_txt != "litros" else min(max(unidades, 1), 8)
    st.caption("Marca conforme vas avanzando. (Se reinicia si recargas la página)")

    checks = []
    cols = st.columns(4)
    for i in range(max_slots):
        with cols[i % 4]:
            checks.append(st.checkbox(f"{i+1}", key=f"chk_{i}"))

    hecho = sum(checks)
    st.progress(min(hecho / max_slots, 1.0))
    st.write(f"Progreso: **{hecho}/{max_slots}**")

    st.markdown("---")
    st.subheader("Horarios sugeridos")
    st.caption("Genera un plan simple para tomar agua durante el día y descárgalo al calendario (.ics).")

    col1, col2, col3 = st.columns(3)
    with col1:
        hora_inicio = st.time_input("Empiezo a tomar agua a las", value=datetime.strptime("08:00", "%H:%M").time())
    with col2:
        intervalo_h = st.selectbox("Cada cuántas horas", [2, 3], index=0)
    with col3:
        duracion_min = st.selectbox("Duración del recordatorio (min)", [5, 10, 15], index=1)

    # Cantidad de recordatorios según horas despierta
    # (p.ej. 14h / 2h = 7 recordatorios)
    count = max(1, int(round(horas_despierta / intervalo_h)))

    hoy = datetime.now()
    start_dt = datetime.combine(hoy.date(), hora_inicio)

    # Texto para mostrar horario
    horarios = [(start_dt + timedelta(hours=i * intervalo_h)).strftime("%I:%M %p") for i in range(count)]

    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.write(f"Te quedan **{count} recordatorios** hoy (cada {intervalo_h} horas).")
    st.write("Horarios sugeridos:")
    st.write(" • " + "  |  ".join(horarios))
    st.markdown('</div>', unsafe_allow_html=True)

    ics_bytes = build_ics(
        title="💧 Toma agua (BUMP)",
        start_dt=start_dt,
        duration_min=duracion_min,
        count=count,
        interval_hours=intervalo_h
    )

    st.download_button(
        "⬇️ Descargar recordatorios para Calendario (.ics)",
        data=ics_bytes,
        file_name="bump_recordatorios_agua.ics",
        mime="text/calendar"
    )

    st.caption("Tip: abre el .ics en tu celular y ‘Agregar a Calendario’ para que te aparezcan los recordatorios.")
