import streamlit as st
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from io import BytesIO

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# ------------------ Storage ------------------
DATA_DIR = Path("data_bump")
DATA_DIR.mkdir(exist_ok=True)
JOURNAL_FILE = DATA_DIR / "journal.json"

# ------------------ Fórmulas ------------------
def mifflin_women_bmr(weight_kg: float, height_cm: float, age: int) -> float:
    # GEB mujeres = (10*kg) + (6.25*cm) - (5*edad) - 161
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

ACTIVITY_FACTORS = {
    "Sedentaria (1.2)": 1.2,
    "Ligera 1–3 días/sem (1.375)": 1.375,
    "Moderada 3–5 días/sem (1.55)": 1.55,
    "Intensa 6–7 días/sem (1.725)": 1.725,
    "Muy intensa / trabajo físico (1.9)": 1.9,
}

# Proteína automática según actividad (mínimo > 1.2 => arrancamos en 1.3 g/kg)
def protein_factor_from_activity(activity_factor: float) -> float:
    if activity_factor <= 1.375:
        return 1.3
    elif activity_factor <= 1.55:
        return 1.5
    elif activity_factor <= 1.725:
        return 1.7
    else:
        return 1.9

WATER_PRESETS = {
    "30 ml/kg": 30,
    "35 ml/kg": 35,
}

# ------------------ Diario ------------------
def load_journal():
    if JOURNAL_FILE.exists():
        return json.loads(JOURNAL_FILE.read_text(encoding="utf-8"))
    return []

def save_journal(entries):
    JOURNAL_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

def journal_to_pdf_bytes(entries):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "TFRM BUMP — Diario de Agradecimiento")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 25

    if not entries:
        c.drawString(50, y, "No hay entradas aún.")
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    for idx, e in enumerate(entries, start=1):
        fecha = e.get("timestamp", "").replace("T", " ")
        grat = e.get("gratitud", [])
        note = e.get("nota", "")

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, f"Entrada #{idx} — {fecha}")
        y -= 16

        c.setFont("Helvetica", 10)
        for i, g in enumerate(grat, start=1):
            c.drawString(65, y, f"{i}) {g}")
            y -= 14

        if note:
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(65, y, f"Nota: {note[:120]}")
            y -= 14

        y -= 8

        # salto de página
        if y < 80:
            c.showPage()
            y = height - 50

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ------------------ UI ------------------
st.set_page_config(page_title="TFRM BUMP — Panel de Control", layout="wide")

st.title("TFRM BUMP — Panel de Control")
st.caption("Calorías (GET) + Proteína + Agua + Diario de Agradecimiento")

tab1, tab2 = st.tabs(["📊 Panel", "📝 Diario"])

# ---------- TAB 1: Panel ----------
with tab1:
    colA, colB = st.columns([1, 1])

    with colA:
        st.subheader("Datos")
        age = st.number_input("Edad (años)", min_value=12, max_value=90, value=35, step=1)
        weight = st.number_input("Peso (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.1)
        height = st.number_input("Estatura (cm)", min_value=120.0, max_value=220.0, value=160.0, step=0.5)

        activity_label = st.selectbox("Actividad física", list(ACTIVITY_FACTORS.keys()), index=2)
        activity_factor = ACTIVITY_FACTORS[activity_label]

        st.divider()
        st.subheader("Agua")
        water_label = st.selectbox("Agua (ml/kg)", list(WATER_PRESETS.keys()), index=1)
        water_mlkg = WATER_PRESETS[water_label]

    with colB:
        st.subheader("Resultados")
        bmr = mifflin_women_bmr(weight, height, age)
        get = bmr * activity_factor

        protein_factor = protein_factor_from_activity(activity_factor)
        protein_g = weight * protein_factor

        water_ml = weight * water_mlkg
        water_l = water_ml / 1000

        k1, k2, k3 = st.columns(3)
        k1.metric("GEB (Mifflin)", f"{bmr:,.0f} kcal")
        k2.metric("GET (con actividad)", f"{get:,.0f} kcal")
        k3.metric("Proteína", f"{protein_g:,.0f} g/día")

        st.write("")
        st.info(
            f"**Actividad:** {activity_factor}  \n"
            f"**Proteína automática:** {protein_factor} g/kg  \n"
            f"**Agua:** {water_ml:,.0f} ml/día (**{water_l:,.2f} L**) — {water_mlkg} ml/kg"
        )

        snapshot = pd.DataFrame([{
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "edad": age,
            "peso_kg": weight,
            "estatura_cm": height,
            "actividad": activity_label,
            "factor_actividad": activity_factor,
            "GEB_kcal": round(bmr, 0),
            "GET_kcal": round(get, 0),
            "proteina_g": round(protein_g, 0),
            "proteina_factor_gkg": protein_factor,
            "agua_ml": round(water_ml, 0),
            "agua_mlkg": water_mlkg,
        }])

        st.download_button(
            "⬇️ Descargar cálculo (CSV)",
            data=snapshot.to_csv(index=False).encode("utf-8"),
            file_name="tfrm_bump_calculo.csv",
            mime="text/csv"
        )

# ---------- TAB 2: Diario ----------
with tab2:
    st.subheader("Diario de agradecimiento")
    st.caption("5 agradecimientos + historial + export a PDF")

    entries = load_journal()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Hoy agradezco:**")
        a1 = st.text_input("1)", "")
        a2 = st.text_input("2)", "")
        a3 = st.text_input("3)", "")
        a4 = st.text_input("4)", "")
        a5 = st.text_input("5)", "")
        note = st.text_area("Nota (opcional)", "", height=90)

        if st.button("💾 Guardar entrada"):
            new_entry = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "gratitud": [x for x in [a1, a2, a3, a4, a5] if x.strip()],
                "nota": note.strip()
            }
            entries.insert(0, new_entry)
            save_journal(entries)
            st.success("Entrada guardada.")

        pdf_bytes = journal_to_pdf_bytes(entries)
        st.download_button(
            "⬇️ Descargar diario (PDF)",
            data=pdf_bytes,
            file_name="tfrm_bump_diario.pdf",
            mime="application/pdf"
        )

    with col2:
        st.markdown("**Historial**")
        if entries:
            df = pd.DataFrame([{
                "fecha": e["timestamp"].replace("T", " "),
                "gratitud": " | ".join(e.get("gratitud", [])),
                "nota": e.get("nota", "")
            } for e in entries])

            st.dataframe(df, use_container_width=True, height=360)

            st.download_button(
                "⬇️ Descargar historial (CSV)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="tfrm_bump_journal.csv",
                mime="text/csv"
            )
        else:
            st.write("Aún no hay entradas.")
