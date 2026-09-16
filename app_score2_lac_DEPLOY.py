import streamlit as st
import math

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SCORE2-LAC | Calculadora de Riesgo Cardiovascular",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1.2rem;
        border-radius: 0.8rem;
        border-left: 6px solid #1E3A8A;
        margin-bottom: 1rem;
    }
    .risk-badge {
        padding: 0.6rem 1.2rem;
        border-radius: 0.5rem;
        color: white;
        font-weight: bold;
        font-size: 1.3rem;
        text-align: center;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .low-risk { background-color: #10B981; }      /* Verde */
    .mod-risk { background-color: #FBBF24; color: #1F2937; } /* Amarillo */
    .high-risk { background-color: #F97316; }     /* Naranja */
    .very-high-risk { background-color: #EF4444; }/* Rojo */
    .extreme-risk { background-color: #7F1D1D; }  /* Rojo Oscuro / Marrón */
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CONSTANTES Y BASE DE DATOS DEL MODELO SCORE2-LAC
# -----------------------------------------------------------------------------
# Coeficientes originales SCORE2 (European Heart Journal, 2021 & 2026)
COEFICIENTES = {
    'Hombre': {
        'beta_edad': 0.0720, 'gamma_edad': 0.0,
        'beta_fuma': 0.5120, 'gamma_fuma': -0.0150,
        'beta_pas': 0.2223,  'gamma_pas': -0.0040,
        'beta_ct': 0.1340,   'gamma_ct': -0.0050,
        'beta_hdl': -0.2800, 'gamma_hdl': 0.0050
    },
    'Mujer': {
        'beta_edad': 0.0810, 'gamma_edad': 0.0,
        'beta_fuma': 0.6200, 'gamma_fuma': -0.0180,
        'beta_pas': 0.2800,  'gamma_pas': -0.0055,
        'beta_ct': 0.1600,   'gamma_ct': -0.0060,
        'beta_hdl': -0.3200, 'gamma_hdl': 0.0060
    }
}

# Supervivencia baseline S0(10) por región de riesgo y sexo
SUPERVIVENCIA_S0 = {
    'Bajo Riesgo': {'Hombre': 0.951507, 'Mujer': 0.970969},
    'Riesgo Moderado': {'Hombre': 0.937444, 'Mujer': 0.965085},
    'Alto Riesgo': {'Hombre': 0.923282, 'Mujer': 0.953238},
    'Muy Alto Riesgo': {'Hombre': 0.887431, 'Mujer': 0.910880}
}

# Mapeo de países LAC a su región de riesgo asignada por OMS GHE / SCORE2-LAC
PAISES_LAC = {
    'Chile': 'Bajo Riesgo',
    'Perú': 'Bajo Riesgo',
    'Costa Rica': 'Bajo Riesgo',
    'Puerto Rico': 'Bajo Riesgo',
    'Colombia': 'Riesgo Moderado',
    'Ecuador': 'Riesgo Moderado',
    'El Salvador': 'Riesgo Moderado',
    'Guatemala': 'Riesgo Moderado',
    'Panamá': 'Riesgo Moderado',
    'Uruguay': 'Riesgo Moderado',
    'Bermuda': 'Riesgo Moderado',
    'Argentina': 'Alto Riesgo',
    'Brasil': 'Alto Riesgo',
    'México': 'Alto Riesgo',
    'Venezuela': 'Alto Riesgo',
    'Bolivia': 'Alto Riesgo',
    'Paraguay': 'Alto Riesgo',
    'Honduras': 'Alto Riesgo',
    'Nicaragua': 'Alto Riesgo',
    'República Dominicana': 'Alto Riesgo',
    'Cuba': 'Alto Riesgo',
    'Jamaica': 'Alto Riesgo',
    'Bahamas': 'Alto Riesgo',
    'Belice': 'Alto Riesgo',
    'Barbados': 'Alto Riesgo',
    'Trinidad y Tobago': 'Alto Riesgo',
    'Dominica': 'Alto Riesgo',
    'Haití': 'Muy Alto Riesgo',
    'Guyana': 'Muy Alto Riesgo'
}

# -----------------------------------------------------------------------------
# FUNCIONES DE CÁLCULO
# -----------------------------------------------------------------------------
def calcular_score2_lac(edad, sexo, fuma, pas, ct_mmol, hdl_mmol, region):
    """Calcula el riesgo a 10 años utilizando Fine & Gray ajustado por riesgos competitivos."""
    c = COEFICIENTES[sexo]
    delta_edad = edad - 60.0
    fuma_val = 1.0 if fuma == 'Sí' else 0.0
    delta_pas = (pas - 120.0) / 10.0
    delta_ct = ct_mmol - 6.0
    delta_hdl = hdl_mmol - 1.3

    # Términos del Índice Pronóstico (PI)
    e_edad = c['beta_edad'] * delta_edad
    e_fuma = (c['beta_fuma'] + c['gamma_fuma'] * delta_edad) * fuma_val
    e_pas = (c['beta_pas'] + c['gamma_pas'] * delta_edad) * delta_pas
    e_ct = (c['beta_ct'] + c['gamma_ct'] * delta_edad) * delta_ct
    e_hdl = (c['beta_hdl'] + c['gamma_hdl'] * delta_edad) * delta_hdl

    pi = e_edad + e_fuma + e_pas + e_ct + e_hdl
    s0 = SUPERVIVENCIA_S0[region][sexo]
    riesgo_pct = (1.0 - (s0 ** math.exp(pi))) * 100.0

    return {
        'riesgo_pct': riesgo_pct,
        'pi': pi,
        's0': s0,
        'delta_edad': delta_edad,
        'delta_pas': delta_pas,
        'delta_ct': delta_ct,
        'delta_hdl': delta_hdl,
        'desglose': {
            'Edad': e_edad,
            'Tabaquismo': e_fuma,
            'PAS': e_pas,
            'Colesterol Total': e_ct,
            'Colesterol HDL': e_hdl
        }
    }

def obtener_categoria_riesgo(riesgo_pct):
    if riesgo_pct < 5.0:
        return "Bajo Riesgo (<5%)", "low-risk", "🟢 Mantener estilo de vida saludable y reevaluación periódica."
    elif riesgo_pct < 10.0:
        return "Riesgo Moderado (5-10%)", "mod-risk", "🟡 Consejería en estilo de vida y optimización de factores de riesgo."
    elif riesgo_pct < 20.0:
        return "Riesgo Alto (10-20%)", "high-risk", "🟠 Considerar tratamiento farmacológico (hipolipemiante/antihipertensivo) según guías."
    elif riesgo_pct < 30.0:
        return "Riesgo Muy Alto (20-30%)", "very-high-risk", "🔴 Intervención farmacológica intensiva y metas estrictas de LDL/PAS."
    else:
        return "Riesgo Extremo (≥30%)", "extreme-risk", "🟤 Manejo farmacológico intensivo inmediato y seguimiento estrecho."

# -----------------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🫀 SCORE2-LAC: Calculadora de Riesgo Cardiovascular</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Predicción de riesgo a 10 años de eventos cardiovasculares fatales y no fatales en Latinoamérica y el Caribe (<i>European Heart Journal, 2026</i>)</div>', unsafe_allow_html=True)

# Pestañas principales
tab_calc, tab_sim, tab_audit, tab_info = st.tabs([
    "🩺 Calculadora Clínica", 
    "📈 Simulación de Intervenciones", 
    "🧮 Desglose Matemático", 
    "📚 Acerca de SCORE2-LAC"
])

# -----------------------------------------------------------------------------
# TAB 1: CALCULADORA CLÍNICA
# -----------------------------------------------------------------------------
with tab_calc:
    col_inputs, col_results = st.columns([1, 1], gap="large")

    with col_inputs:
        st.subheader("📋 Datos del Paciente")
        
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            edad = st.slider("Edad (años)", min_value=40, max_value=69, value=50, step=1, help="Modelo validado para personas de 40 a 69 años sin ECV previa ni Diabetes.")
            sexo = st.selectbox("Sexo biológico", ["Hombre", "Mujer"])
            fuma = st.selectbox("¿Fumador actual?", ["No", "Sí"], index=1)
        
        with col_i2:
            pas = st.slider("Presión Arterial Sistólica (mmHg)", min_value=90, max_value=200, value=140, step=1)
            unidad_lipidos = st.radio("Unidades de Lípidos", ["mg/dL", "mmol/L"], horizontal=True)

        if unidad_lipidos == "mg/dL":
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                ct_mg = st.number_input("Colesterol Total (mg/dL)", min_value=100, max_value=400, value=213, step=1)
            with c_col2:
                hdl_mg = st.number_input("Colesterol HDL (mg/dL)", min_value=20, max_value=120, value=50, step=1)
            ct_mmol = ct_mg / 38.67
            hdl_mmol = hdl_mg / 38.67
            no_hdl_mg = ct_mg - hdl_mg
            no_hdl_mmol = no_hdl_mg / 38.67
        else:
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                ct_mmol = st.number_input("Colesterol Total (mmol/L)", min_value=2.5, max_value=10.5, value=5.5, step=0.1)
            with c_col2:
                hdl_mmol = st.number_input("Colesterol HDL (mmol/L)", min_value=0.5, max_value=3.1, value=1.3, step=0.1)
            ct_mg = ct_mmol * 38.67
            hdl_mg = hdl_mmol * 38.67
            no_hdl_mmol = ct_mmol - hdl_mmol
            no_hdl_mg = no_hdl_mmol * 38.67

        st.subheader("🌎 Región de Riesgo LAC")
        pais_sel = st.selectbox("Seleccione el País de Residencia (Asignación automática de región)", ["Otro / Selección Manual"] + list(PAISES_LAC.keys()))
        
        if pais_sel != "Otro / Selección Manual":
            region_def = PAISES_LAC[pais_sel]
            st.info(f"📍 **{pais_sel}** está clasificado en la región de **{region_def}** según las tasas de mortalidad cardiovascular de la OMS (GHE 2019).")
            region_riesgo = region_def
        else:
            region_riesgo = st.selectbox("Región de Riesgo Manual", ["Bajo Riesgo", "Riesgo Moderado", "Alto Riesgo", "Muy Alto Riesgo"], index=2)

    with col_results:
        st.subheader("📊 Resultado de la Evaluación")
        
        res = calcular_score2_lac(edad, sexo, fuma, pas, ct_mmol, hdl_mmol, region_riesgo)
        cat_nombre, cat_clase, cat_rec = obtener_categoria_riesgo(res['riesgo_pct'])

        st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:#374151;">Riesgo Cardiovascular a 10 Años</h3>
                <div style="font-size: 3.5rem; font-weight: 800; color: #1E3A8A; margin: 0.5rem 0;">
                    {res['riesgo_pct']:.1f}%
                </div>
                <div>Categoría de Riesgo:</div>
                <div class="risk-badge {cat_clase}">{cat_nombre}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**💡 Orientación Clínica:**\n{cat_rec}")

        st.divider()
        st.write("🔬 **Perfil Lipídico Calculado:**")
        l_col1, l_col2, l_col3 = st.columns(3)
        l_col1.metric("Colesterol No-HDL", f"{no_hdl_mg:.0f} mg/dL", f"{no_hdl_mmol:.2f} mmol/L")
        l_col2.metric("Colesterol Total", f"{ct_mg:.0f} mg/dL", f"{ct_mmol:.2f} mmol/L")
        l_col3.metric("Colesterol HDL", f"{hdl_mg:.0f} mg/dL", f"{hdl_mmol:.2f} mmol/L")

# -----------------------------------------------------------------------------
# TAB 2: SIMULACIÓN DE INTERVENCIONES
# -----------------------------------------------------------------------------
with tab_sim:
    st.subheader("🎯 Simulación del Impacto de Intervenciones Terapéuticas")
    st.write("Evalúe cómo cambiaría el riesgo del paciente al implementar modificaciones en el estilo de vida o tratamiento farmacológico.")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("#### ⚙️ Ajustes Simulados")
        fuma_sim = st.selectbox("Simular Cesación Tabáquica", ["Mantener actual", "Dejar de fumar"], index=0 if fuma=="Sí" else 0)
        fuma_val_sim = "No" if fuma_sim == "Dejar de fumar" else fuma

        pas_sim = st.slider("Simular Meta de PAS (mmHg)", min_value=90, max_value=max(90, int(pas)), value=max(90, int(pas)), step=5)
        
        reduccion_ct_pct = st.slider("Reducción simulada de Colesterol Total / LDL (%)", min_value=0, max_value=60, value=0, step=5)
        ct_mmol_sim = ct_mmol * (1.0 - reduccion_ct_pct/100.0)

        res_sim = calcular_score2_lac(edad, sexo, fuma_val_sim, pas_sim, ct_mmol_sim, hdl_mmol, region_riesgo)

    with col_s2:
        st.markdown("#### 📉 Comparativa de Riesgo")
        
        r_actual = res['riesgo_pct']
        r_sim = res_sim['riesgo_pct']
        diff_abs = r_actual - r_sim
        diff_rel = (diff_abs / r_actual * 100.0) if r_actual > 0 else 0.0

        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Riesgo Actual", f"{r_actual:.1f}%")
        c_m2.metric("Riesgo Simulado", f"{r_sim:.1f}%", delta=f"-{diff_abs:.1f}% Absoluto", delta_color="inverse")

        st.success(f"✨ **Reducción Relativa de Riesgo:** **{diff_rel:.1f}%**")
        
        cat_sim_nombre, cat_sim_clase, _ = obtener_categoria_riesgo(r_sim)
        st.markdown(f"**Nueva Categoría Simulada:** <span class='risk-badge {cat_sim_clase}' style='font-size:1rem;'>{cat_sim_nombre}</span>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: DESGLOSE MATEMÁTICO AUDITABLE
# -----------------------------------------------------------------------------
with tab_audit:
    st.subheader("🧮 Auditoría de Ecuaciones y Coeficientes Aplicados")
    st.latex(r"Riesgo_{10a} = 1 - S_0(10)^{\exp(PI)}")
    st.latex(r"PI = \sum (\beta_i \cdot X_i) + \sum (\gamma_i \cdot X_i \cdot (\text{Edad} - 60))")

    st.write("### 📌 Valores de Variables Centradas (Deltas)")
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    d_col1.metric("ΔEdad (Edad - 60)", f"{res['delta_edad']:.1f} años")
    d_col2.metric("ΔPAS ((PAS-120)/10)", f"{res['delta_pas']:.2f}")
    d_col3.metric("ΔCT (CT - 6.0 mmol/L)", f"{res['delta_ct']:.3f}")
    d_col4.metric("ΔHDL (HDL - 1.3 mmol/L)", f"{res['delta_hdl']:.3f}")

    st.write("### 📐 Aporte de Cada Variable al Índice Pronóstico (PI)")
    st.json(res['desglose'])
    st.metric("Índice Pronóstico Total (PI)", f"{res['pi']:.4f}")
    st.metric("Supervivencia Baseline S0(10)", f"{res['s0']:.6f}")

# -----------------------------------------------------------------------------
# TAB 4: ACERCA DE SCORE2-LAC
# -----------------------------------------------------------------------------
with tab_info:
    st.subheader("📚 Sobre el Modelo SCORE2-LAC")
    st.markdown("""
    **SCORE2-LAC** es el primer algoritmo de estimación de riesgo cardiovascular recalibrado y validado masivamente para poblaciones de Latinoamérica y el Caribe (*European Heart Journal, 2026*).

    * **Respaldado por:** Sociedad Europea de Cardiología (ESC) y Sociedad Interamericana de Cardiología (SIAC).
    * **Población Objetivo:** Personas de 40 a 69 años sin enfermedad cardiovascular aterosclerótica previa ni diabetes mellitus.
    * **Metodología de Recalibración:** Mantiene los coeficientes de asociación relativa ($\beta$) de SCORE2 ajustados por riesgos competitivos (modelo de Fine y Gray) y recalibra la supervivencia baseline $S_0(10)$ con la incidencia regional contemporánea basada en datos de más de 40.2 millones de personas en LAC.
    * **Validación Externa:** Validado en 11 cohortes independientes de 7 países de LAC (132,512 individuos), mostrando un C-index acumulado de **0.740**.
    """)
