import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ranking das cidades", layout="wide")

st.markdown(""" 
<style>
/* Import fun and expressive fonts */
@import url('https://fonts.googleapis.com/css2?family=Bungee&family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

body {
    justify: center;
}            

.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

/* Updated Fun Title Font */
.titulo {
    text-align: center;
    font-family: 'Bungee', cursive;
    font-size: 3rem;
    color: #1E1E1E;
    letter-spacing: 0.02em;
    margin-bottom: 0rem;
    text-transform: uppercase;
}

.subtitulo {
    text-align: center;
    font-family: 'DM Sans', sans-serif;
    font-size: 1.1rem;
    margin-bottom: 2rem;
    opacity: 0.7;
}

.section-label {
    text-align: center;
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    opacity: 0.6;
}

/* Button Centering & Fun Styling */
div[data-testid="stButton"] {
    display: flex;
    justify-content: center;
    margin-top: 1.5rem;
}

div[data-testid="stButton"] > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase;
    border: 2px solid #1E1E1E !important;
    border-radius: 50px !important; /* Pill shape is more 'fun' */
    padding: 0.6rem 3rem !important;
    background-color: transparent !important;
    color: #1E1E1E !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

div[data-testid="stButton"] > button:hover {
    background-color: #1E1E1E !important;
    color: white !important;
    transform: scale(1.05); /* Slight pop effect */
}

/* Clean Dataframe Styling */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    border: 1px solid #f0f2f6;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="titulo">Onde devo ir morar? 🤔</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Rankeie cidades conforme o que importa pra você.</div>', unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # Dados das cidades
    df = pd.read_csv("CIDADES.csv", header=0)
    df.columns = ["cidade", "qualidade_vida", "lazer_natural", "custo", "seguranca", "descricao"]
    
    # Matriz de distâncias
    dist_matriz = pd.read_csv("DISTANCIAS.csv", index_col=0)
    return df, dist_matriz

try:
    df_original, df_dist = load_data()
except FileNotFoundError:
    st.error("Arquivos 'CIDADES.csv' ou 'DISTANCIAS.csv' não encontrados.")
    st.stop()

# ── Global Settings ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">📍 Ponto de Partida</div>', unsafe_allow_html=True)
cidade_referencia = st.selectbox("Selecione a cidade onde você mora atualmente:", df_dist.index.tolist())

st.divider()

# ── Weights form ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">🎛️ O que importa pra você? (1 = pouco, 5 = muito)</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    w_qv    = st.number_input("Qualidade de vida",  min_value=1, max_value=5, value=1, step=1)
with c2:
    w_ln    = st.number_input("Lazer natural",       min_value=1, max_value=5, value=1, step=1)
with c3:
    w_custo = st.number_input("Custo de vida",       min_value=1, max_value=5, value=1, step=1)
with c4:
    w_seg   = st.number_input("Segurança",           min_value=1, max_value=5, value=1, step=1)
with c5:
    w_dist  = st.number_input(f"Proximidade de {cidade_referencia}",   min_value=1, max_value=5, value=1, step=1)

# --- CHANGED SECTION FOR CENTERING ---
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn2:
    calcular = st.button("⚡ Calcular ranking", width="content")
# -------------------------------------

st.divider()

# ── Editable table ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Tabela de cidades</div>', unsafe_allow_html=True)
st.caption("Valores gerados por IA, mas podem ser editados antes de você calcular.")

edited_df = st.data_editor(
    df_original,
    width='content',
    num_rows="dynamic",
    column_config={
        "cidade":         st.column_config.TextColumn("Cidade"),
        "qualidade_vida": st.column_config.NumberColumn("Qualidade de vida", min_value=0, max_value=5),
        "lazer_natural":  st.column_config.NumberColumn("Lazer natural",      min_value=0, max_value=5),
        "custo":          st.column_config.NumberColumn("Custo de vida",      min_value=0, max_value=5),
        "seguranca":      st.column_config.NumberColumn("Segurança",          min_value=0, max_value=5),
        "descricao":      st.column_config.TextColumn("Descrição"),
    },
    hide_index=True,
    key="tabela_cidades",
)

# ── Ranking Logic ─────────────────────────────────────────────────────────────
if calcular:
    importances = {
        "qualidade_vida": w_qv,
        "lazer_natural":  w_ln,
        "custo":          w_custo,
        "seguranca":      w_seg,
        "proximidade":    w_dist,
    }
    
    total_importance = sum(importances.values())

    def get_rank(row):
        try:
            dist = df_dist.loc[cidade_referencia, row['cidade']]
        except:
            dist = 5000 

        score_proximidade = max(0, (1 - (dist / 4000)) * 10)
        
        weighted_sum = (
            (row['qualidade_vida'] * importances['qualidade_vida']) +
            (row['lazer_natural'] * importances['lazer_natural']) +
            (row['custo'] * importances['custo']) +
            (row['seguranca'] * importances['seguranca']) +
            (score_proximidade * importances['proximidade'])
        )
        return weighted_sum / total_importance, dist

    result_df = edited_df.copy()
    res_apply = result_df.apply(get_rank, axis=1)
    result_df["score"] = res_apply.apply(lambda x: round(x[0], 2))
    result_df["distancia_real"] = res_apply.apply(lambda x: x[1])
    
    result_df = result_df.sort_values("score", ascending=False).reset_index(drop=True)
    result_df.insert(0, "rank", result_df.index + 1)

    st.divider()
    st.markdown(f'<div class="rank-header">🏆 Ranking final (Referência: {cidade_referencia})</div>', unsafe_allow_html=True)

    st.dataframe(
        result_df,
        width='content',
        hide_index=True,
        column_config={
            "rank":           st.column_config.NumberColumn("#", width="small"),
            "cidade":         st.column_config.TextColumn("Cidade"),
            "score":          st.column_config.ProgressColumn("Score Total", min_value=0, max_value=5, format="%.2f"),
            "distancia_real": st.column_config.NumberColumn(f"Distância de {cidade_referencia} (km)"),
            "qualidade_vida": st.column_config.NumberColumn("Q.V."),
            "lazer_natural":  st.column_config.NumberColumn("Lazer"),
            "custo":          st.column_config.NumberColumn("Custo"),
            "seguranca":      st.column_config.NumberColumn("Seg."),
        },
    )

    top = result_df.iloc[1]
    st.success(f"🥇 Segunda melhor opção para quem está em **{cidade_referencia}**: **{top['cidade']}**")