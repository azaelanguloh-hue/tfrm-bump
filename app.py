import streamlit as st
from datetime import datetime, timedelta

# -----------------------------
# Config (sin BUMP)
# -----------------------------
st.set_page_config(
    page_title="TFRM — Panel de Control",
    layout="centered",
    page_icon="🌿"
)

# -----------------------------
# Estilos (limpio, amigable)
# -----------------------------
st.markdown("""
<style>
.big-card{
  padding:18px; border-radius:16px;
  border:1px solid rgba(0,0,0,0.08);
  background:rgba(255,255,255,0.78);
}
.kpi{ font-size:2rem; font-weight:800; line-height:1.1; }
.kpi-sub{ font-size:0.95rem; opacity:0.82; }
.small-note{ font-size:0.95rem; opacity:0.82; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Reglas / Fórmulas
# -----------------------------
ACTIVITY_LEVELS = {
    "Sedentaria (1.2)": 1.2,
    "Ligera 1–3 días/sem (1.375)": 1.375,
    "Moderada 3–5 días/sem (1.55)": 1.55,
    "Intensa 6–7 días/sem (1.725)": 1.725,
    "Muy intensa / trabajo físico (1.9)": 1.9,
}

# ✅ Session state: guardar nivel de actividad para todos los tabs
if "nivel_actividad_label" not in st.session_state:
    st.session_state["nivel_actividad_label"] = "Moderada 3–5 días/sem (1.55)"

def mifflin_women_bmr(weight_kg: float, height_cm: float, age: int) -> float:
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

def protein_factor_from_days(days: int) -> float:
    if days <= 3:
        return 1.3
    if days <= 5:
        return 1.5
    return 1.7

def activity_reco_text(days: int) -> str:
    if days == 0:
        return "Meta mínima sugerida: 3 días/semana (20–30 min)."
    if days <= 2:
        return "Vas en camino: sube a 3 días/semana para crear consistencia."
    if days == 3:
        return "Bien: si puedes, sube a 4 días/semana."
    if days == 4:
        return "Excelente: si te sientes bien, apunta a 5 días/semana."
    if days == 5:
        return "Perfecto: mantén 5 días/semana."
    return "Alto nivel: cuida sueño y 1 día suave/recuperación."

def water_mlkg_from_activity_factor(activity_factor: float) -> int:
    return 30 if activity_factor <= 1.375 else 35

def build_ics(title: str, start_dt: datetime, duration_min: int, count: int, interval_hours: int):
    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%S")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TFRM//PanelControl//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    uid_base = f"{int(datetime.now().timestamp())}@tfrm-panel"
    now = datetime.now()
    for i in range(count):
        s = start_dt + timedelta(hours=i * interval_hours)
        e = s + timedelta(minutes=duration_min)
        uid = f"{uid_base}-{i}"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{fmt(now)}",
            f"DTSTART:{fmt(s)}",
            f"DTEND:{fmt(e)}",
            f"SUMMARY:{title}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\n".join(lines).encode("utf-8")

PROTEIN_FOODS = [
    {"alimento": "Pechuga de pollo cocida", "porcion": "100 g", "proteina_g": 31},
    {"alimento": "Pavo cocido", "porcion": "100 g", "proteina_g": 29},
    {"alimento": "Atún en agua (lata)", "porcion": "1 lata (~120 g drenado)", "proteina_g": 26},
    {"alimento": "Salmón", "porcion": "100 g", "proteina_g": 22},
    {"alimento": "Huevo", "porcion": "1 pieza", "proteina_g": 6},
    {"alimento": "Claras", "porcion": "3 claras", "proteina_g": 11},
    {"alimento": "Yogur griego natural", "porcion": "170 g", "proteina_g": 17},
    {"alimento": "Requesón / cottage", "porcion": "1/2 taza", "proteina_g": 14},
    {"alimento": "Queso panela", "porcion": "60 g", "proteina_g": 12},
    {"alimento": "Frijoles cocidos", "porcion": "1 taza", "proteina_g": 15},
    {"alimento": "Lentejas cocidas", "porcion": "1 taza", "proteina_g": 18},
    {"alimento": "Tofu", "porcion": "150 g", "proteina_g": 18},
]

# -----------------------------
# UI
# -----------------------------
st.title("TFRM — Panel de Control")
st.caption("Agua • Proteína • Calorías • Actividad (simple, claro y usable diario)")

tab1, tab2, tab3 = st.tabs(["📌 Panel", "🍗 Proteína (alimentos)", "⏰ Recordatorios"])

# -----------------------------
# TAB 1: Panel
# -----------------------------
with tab1:
    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.subheader("Tus datos")

    colA, colB = st.columns(2)
    with colA:
        edad = st.number_input("Edad (años)", min_value=12, max_value=90, value=35, step=1)
        peso_kg = st.number_input("Peso (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.1)
    with colB:
        estatura_cm = st.number_input("Estatura (cm)", min_value=120, max_value=220, value=160, step=1)
        dias_ejercicio = st.slider("Días de actividad física por semana", 0, 7, 3)

    # ✅ Nivel de actividad compartido (se guarda y se reutiliza)
    nivel_actividad_label = st.selectbox(
        "Nivel de actividad (para calcular calorías y agua)",
        list(ACTIVITY_LEVELS.keys()),
        index=list(ACTIVITY_LEVELS.keys()).index(st.session_state["nivel_actividad_label"]),
        key="nivel_actividad_global"
    )
    st.session_state["nivel_actividad_label"] = nivel_actividad_label
    activity_factor = ACTIVITY_LEVELS[nivel_actividad_label]

    mlkg = water_mlkg_from_activity_factor(activity_factor)

    st.markdown(
        f'<p class="small-note">Agua asignada automáticamente por tu nivel: <b>{mlkg} ml/kg</b> (máximo 35 ml/kg).</p>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Cálculos
    agua_ml = peso_kg * mlkg
    agua_l = agua_ml / 1000

    protein_factor = protein_factor_from_days(dias_ejercicio)
    proteina_g = peso_kg * protein_factor

    bmr = mifflin_women_bmr(peso_kg, estatura_cm, edad)
    calorias = bmr * activity_factor

    st.markdown("---")
    st.subheader("Tus resultados")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="big-card">', unsafe_allow_html=True)
        st.markdown("💧 **Agua recomendada**")
        st.markdown(f'<div class="kpi">{agua_l:.2f} L</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-sub">({agua_ml:,.0f} ml/día • {mlkg} ml/kg)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="big-card">', unsafe_allow_html=True)
        st.markdown("🍗 **Proteína recomendada**")
        st.markdown(f'<div class="kpi">{proteina_g:,.0f} g</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-sub">({protein_factor} g/kg según tus días de actividad)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.markdown("🔥 **Calorías diarias estimadas**")
    st.markdown(f'<div class="kpi">{calorias:,.0f} kcal</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="kpi-sub">Basado en edad, peso, estatura y nivel: <b>{nivel_actividad_label}</b></div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("")
st.markdown('<div class="big-card">', unsafe_allow_html=True)
st.markdown("🏃‍♀️ **Actividad física**")
st.write(f"**Sugerencia:** {activity_reco_text(dias_ejercicio)}")
st.markdown('</div>', unsafe_allow_html=True)
st.caption("Educativo y de apoyo. Si estás embarazada/lactando o con condiciones médicas, consulta a un profesional.")

# -----------------------------
# TAB 2: Proteína (alimentos)
# -----------------------------
with tab2:
    st.subheader("Guía rápida de proteína por alimentos")
    st.caption("Aproximaciones por porción común para ayudar a llegar a tu meta diaria.")

    col1, col2 = st.columns(2)
    with col1:
        peso2 = st.number_input("Tu peso (kg) (para estimar meta)", min_value=30.0, max_value=250.0, value=70.0, step=0.1, key="peso_tab2")
    with col2:
        dias2 = st.slider("Días de actividad por semana", 0, 7, 3, key="dias_tab2")

    # ✅ Muestra el nivel global (sin pedirlo otra vez)
    st.markdown(
        f'<p class="small-note">Nivel de actividad seleccionado: <b>{st.session_state["nivel_actividad_label"]}</b></p>',
        unsafe_allow_html=True
    )

    protein_factor2 = protein_factor_from_days(dias2)
    meta_prot = peso2 * protein_factor2

    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.markdown("🎯 **Tu meta diaria estimada**")
    st.markdown(f'<div class="kpi">{meta_prot:,.0f} g de proteína</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-sub">{protein_factor2} g/kg según {dias2} días/semana</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    rows = []
    for item in PROTEIN_FOODS:
        rows.append([item["alimento"], item["porcion"], item["proteina_g"]])
    st.dataframe(rows, use_container_width=True, hide_index=True,
                 column_config={
                     0: st.column_config.TextColumn("Alimento"),
                     1: st.column_config.TextColumn("Porción"),
                     2: st.column_config.NumberColumn("Proteína (g)")
                 })

    st.markdown("---")
    st.subheader("¿Cuántas porciones te faltan?")
    st.caption("Elige un alimento y te digo cuántas porciones aproximadas serían para alcanzar tu meta.")

    opciones = [f'{x["alimento"]} — {x["porcion"]} (~{x["proteina_g"]} g)' for x in PROTEIN_FOODS]
    sel = st.selectbox("Selecciona un alimento", opciones, index=0)

    idx = opciones.index(sel)
    prot_por_porcion = PROTEIN_FOODS[idx]["proteina_g"]

    llevas = st.number_input("¿Cuánta proteína ya llevas hoy? (g)", min_value=0.0, max_value=400.0, value=0.0, step=1.0)
    faltan = max(meta_prot - llevas, 0)
    porciones = 0 if prot_por_porcion == 0 else faltan / prot_por_porcion

    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.write(f"Te faltan aprox. **{faltan:,.0f} g** para llegar a tu meta.")
    st.write(f"Eso equivale a **{porciones:.1f} porciones** de: **{PROTEIN_FOODS[idx]['alimento']}**.")
    st.markdown('<p class="small-note">Tip: reparte la proteína en 3–4 comidas para que sea fácil de cumplir.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# TAB 3: Recordatorios (agua)
# -----------------------------
with tab3:
    st.subheader("Recordatorios de agua")
    st.caption("Checklist + horarios sugeridos + archivo para calendario (.ics)")

    colA, colB = st.columns(2)
    with colA:
        peso_r = st.number_input("Tu peso (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.1, key="peso_recordatorios")

        # ✅ Usa el nivel global automáticamente (sin selectbox)
        nivel_actividad_label_r = st.session_state["nivel_actividad_label"]
        activity_factor_r = ACTIVITY_LEVELS[nivel_actividad_label_r]
        mlkg_r = water_mlkg_from_activity_factor(activity_factor_r)

        st.markdown(
            f'<p class="small-note">Nivel de actividad seleccionado: <b>{nivel_actividad_label_r}</b> → Agua: <b>{mlkg_r} ml/kg</b></p>',
            unsafe_allow_html=True
        )

    with colB:
        presentacion = st.selectbox("¿Cómo la mides?", ["Vasos de 250 ml", "Botellas de 500 ml", "Litros"], index=1)
        horas_despierta = st.slider("Horas despierta al día (aprox.)", 10, 18, 14)

    agua_ml_r = peso_r * mlkg_r
    agua_l_r = agua_ml_r / 1000

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

    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.markdown("✅ **Meta de agua de hoy**")
    st.markdown(f'<div class="kpi">{agua_l_r:.2f} L</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="kpi-sub">{agua_ml_r:,.0f} ml/día • {mlkg_r} ml/kg</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div class='kpi-sub'>Según nivel: <b>{nivel_actividad_label_r}</b> • Equivale aprox. a <b>{max(unidades,1)} {unidad_txt}</b>.</div>",
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Checklist rápido")
    st.caption("Marca conforme avanzas (se reinicia si recargas).")

    max_slots = min(max(max(unidades, 1), 1), 12)
    cols = st.columns(4)
    checks = []
    for i in range(max_slots):
        with cols[i % 4]:
            checks.append(st.checkbox(f"{i+1}", key=f"chk_{i}"))
    hecho = sum(checks)
    st.progress(min(hecho / max_slots, 1.0))
    st.write(f"Progreso: **{hecho}/{max_slots}**")

    st.markdown("---")
    st.subheader("Horarios sugeridos")
    col1, col2, col3 = st.columns(3)
    with col1:
        hora_inicio = st.time_input("Empiezo a tomar agua a las", value=datetime.strptime("08:00", "%H:%M").time())
    with col2:
        intervalo_h = st.selectbox("Cada cuántas horas", [2, 3], index=0)
    with col3:
        duracion_min = st.selectbox("Duración del recordatorio (min)", [5, 10, 15], index=1)

    count = max(1, int(round(horas_despierta / intervalo_h)))
    hoy = datetime.now()
    start_dt = datetime.combine(hoy.date(), hora_inicio)
    horarios = [(start_dt + timedelta(hours=i * intervalo_h)).strftime("%I:%M %p") for i in range(count)]

    st.markdown('<div class="big-card">', unsafe_allow_html=True)
    st.write(f"Te quedan **{count} recordatorios** hoy (cada {intervalo_h} horas).")
    st.write(" • " + "  |  ".join(horarios))
    st.markdown('</div>', unsafe_allow_html=True)

    ics_bytes = build_ics(
        title="💧 Agua (TFRM)",
        start_dt=start_dt,
        duration_min=duracion_min,
        count=count,
        interval_hours=intervalo_h
    )
    st.download_button(
        "⬇️ Descargar recordatorios para Calendario (.ics)",
        data=ics_bytes,
        file_name="tfrm_recordatorios_agua.ics",
        mime="text/calendar"
    )

    st.caption("Abre el .ics en tu celular y selecciona “Agregar a Calendario”.")