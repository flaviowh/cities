import streamlit as st
import pandas as pd

st.set_page_config(page_title="Em quais cidades morar?", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: #0f0f13;
    color: #e8e6e0;
}

section[data-testid="stSidebar"] {
    background: #16161d;
    border-right: 1px solid #2a2a36;
}

.block-container {
    padding-top: 2rem;
}

.titulo {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #f0ede6;
    margin-bottom: 0.1rem;
}

.subtitulo {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    color: #6b6b80;
    margin-bottom: 2rem;
}

.score-badge {
    display: inline-block;
    background: linear-gradient(135deg, #c9a84c, #e8c96b);
    color: #0f0f13;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.05em;
}

.stNumberInput > div > div > input {
    background: #1e1e28 !important;
    border: 1px solid #2e2e3e !important;
    color: #e8e6e0 !important;
    border-radius: 6px !important;
}

.stButton > button {
    background: linear-gradient(135deg, #c9a84c, #e8c96b) !important;
    color: #0f0f13 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 2rem !important;
    width: 100%;
    transition: opacity 0.2s;
}

.stButton > button:hover {
    opacity: 0.85 !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #2a2a36;
    border-radius: 10px;
    overflow: hidden;
}

.rank-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #c9a84c;
    margin-bottom: 1rem;
    border-left: 3px solid #c9a84c;
    padding-left: 0.75rem;
}

label[data-testid="stWidgetLabel"] > div > p {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    color: #9999b0;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown('<div class="titulo">Em quais cidades morar?</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Rankeie cidades conforme o que importa pra você.</div>', unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("CIDADES.csv", header=0)
    df.columns = ["cidade", "qualidade_vida", "lazer_natural", "custo", "seguranca", "descricao", "distancia_jp"]
    return df

try:
    df_original = load_data()
except FileNotFoundError:
    st.error("Arquivo 'em quais cidades morar.csv' não encontrado. Coloque-o na mesma pasta que app.py.")
    st.stop()

# ── Sidebar: weights form ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Importâncias")
    st.markdown("<small style='color:#6b6b80'>Quanto cada critério importa pra você? (1 = pouco, 10 = muito)</small>", unsafe_allow_html=True)
    st.markdown("---")

    w_qv   = st.number_input("Qualidade de vida",  min_value=1, max_value=10, value=5, step=1)
    w_ln   = st.number_input("Lazer natural",       min_value=1, max_value=10, value=5, step=1)
    w_custo = st.number_input("Custo de vida",      min_value=1, max_value=10, value=5, step=1)
    w_seg  = st.number_input("Segurança",           min_value=1, max_value=10, value=5, step=1)
    w_dist = st.number_input("Proximidade de JP",   min_value=1, max_value=10, value=5, step=1)

    calcular = st.button("⚡ Calcular ranking")

# ── Editable table ───────────────────────────────────────────────────────────
st.markdown("#### Tabela de cidades")
st.caption("Você pode editar os valores diretamente na tabela antes de calcular.")

edited_df = st.data_editor(
    df_original,
    width=True,
    num_rows="dynamic",
    column_config={
        "cidade":         st.column_config.TextColumn("Cidade"),
        "qualidade_vida": st.column_config.NumberColumn("Qualidade de vida", min_value=0, max_value=10),
        "lazer_natural":  st.column_config.NumberColumn("Lazer natural",      min_value=0, max_value=10),
        "custo":          st.column_config.NumberColumn("Custo de vida",      min_value=0, max_value=10),
        "seguranca":      st.column_config.NumberColumn("Segurança",          min_value=0, max_value=10),
        "descricao":      st.column_config.TextColumn("Descrição"),
        "distancia_jp":   st.column_config.NumberColumn("Distância de JP (km)"),
    },
    hide_index=True,
    key="tabela_cidades",
)

# ── Ranking ──────────────────────────────────────────────────────────────────
if calcular:
    importances = {
        "qualidade_vida": w_qv,
        "lazer_natural":  w_ln,
        "custo":          w_custo,
        "seguranca":      w_seg,
        "distancia_jp":   w_dist,
    }
    total_importance = sum(importances.values())
    max_dist = edited_df["distancia_jp"].max()

    def rank(city):
        weighted_sum = 0
        for k, v in importances.items():
            if k == "distancia_jp":
                normalized_inverse_distance = (1 - (city[k] / max_dist)) * 10
                weighted_sum += v * normalized_inverse_distance
            else:
                weighted_sum += v * city[k]
        return weighted_sum / total_importance

    result_df = edited_df.copy()
    result_df["score"] = result_df.apply(rank, axis=1).round(2)
    result_df = result_df.sort_values("score", ascending=False).reset_index(drop=True)
    result_df.insert(0, "rank", result_df.index + 1)

    st.markdown("---")
    st.markdown('<div class="rank-header">🏆 Ranking final</div>', unsafe_allow_html=True)

    st.dataframe(
        result_df,
        width=True,
        hide_index=True,
        column_config={
            "rank":           st.column_config.NumberColumn("#",               width="small"),
            "cidade":         st.column_config.TextColumn("Cidade"),
            "score":          st.column_config.ProgressColumn("Score", min_value=0, max_value=10, format="%.2f"),
            "qualidade_vida": st.column_config.NumberColumn("Qualidade de vida"),
            "lazer_natural":  st.column_config.NumberColumn("Lazer natural"),
            "custo":          st.column_config.NumberColumn("Custo"),
            "seguranca":      st.column_config.NumberColumn("Segurança"),
            "descricao":      st.column_config.TextColumn("Descrição"),
            "distancia_jp":   st.column_config.NumberColumn("Distância JP (km)"),
        },
    )

    top = result_df.iloc[0]
    st.success(f"🥇 Melhor cidade para você: **{top['cidade']}** — score {top['score']:.2f}")