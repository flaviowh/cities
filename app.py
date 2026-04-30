import streamlit as st
import pandas as pd
import unicodedata
import streamlit.components.v1 as components

def normalize_text(text):
    if not isinstance(text, str):
        return text
    # Remove accents and convert to lowercase
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

st.set_page_config(page_title="Ranking das cidades", layout="wide")

st.markdown(""" 
<style>
@import url('https://fonts.googleapis.com/css2?family=Bungee&family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

.titulo {
    text-align: center;
    font-family: 'Bungee', cursive;
    font-size: 3rem;
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
    border-radius: 50px !important;
    padding: 0.6rem 3rem !important;
    background-color: transparent !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

div[data-testid="stButton"] > button:hover {
    background-color: #1E1E1E !important;
    color: white !important;
    transform: scale(1.05);
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
    border: 1px solid #f0f2f6;
}
</style>
""", unsafe_allow_html=True)

MAX_DISTANCE = 5000
# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="titulo">Onde devo ir morar? 🤔</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Rankeie cidades conforme o que importa pra você.</div>', unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("CITIES.csv", header=0)
    df.columns = ["cidade", "descricao", "qualidade_vida", "custo", "seguranca", "lazer", "natureza"]
    dist_matriz = pd.read_csv("DISTANCIAS.csv", index_col=0)
    dist_matriz.index = dist_matriz.index.map(normalize_text)
    dist_matriz.columns = dist_matriz.columns.map(normalize_text)
    return df, dist_matriz

try:
    df_original, df_dist = load_data()
except FileNotFoundError:
    st.error("Arquivos 'CITIES.csv' ou 'DISTANCIAS.csv' não encontrados.")
    st.stop()

# ── Global Settings ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">📍 Ponto de Partida</div>', unsafe_allow_html=True)
cidade_referencia = st.selectbox("Selecione a cidade onde você mora atualmente:", df_original["cidade"].unique().tolist())

st.divider()

# ── Weights form ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">🎛️ O que importa pra você? (1 = pouco, 5 = muito)</div>', unsafe_allow_html=True)

cols = st.columns(6)
with cols[0]:
    w_qv    = st.number_input("Qualidade Vida",  min_value=1, max_value=5, value=1, step=1)
with cols[1]:
    w_lazer = st.number_input("Lazer",           min_value=1, max_value=5, value=1, step=1)
with cols[2]:
    w_nat   = st.number_input("Natureza",        min_value=1, max_value=5, value=1, step=1)
with cols[3]:
    w_custo = st.number_input("Custo (Barato)",  min_value=1, max_value=5, value=1, step=1)
with cols[4]:
    w_seg   = st.number_input("Segurança",       min_value=1, max_value=5, value=1, step=1)
with cols[5]:
    w_dist  = st.number_input(f"Prox. de {cidade_referencia}", min_value=1, max_value=5, value=1, step=1)

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn2:
    calcular = st.button("💬 Calcular ranking")

st.divider()

# ── Editable table ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Tabela de cidades</div>', unsafe_allow_html=True)
st.caption("Valores da análise combinada de 4 IAs (Gemini, Grok, Chatgpt, Claude). Você pode editá-los antes de calcular.")

edited_df = st.data_editor(
    df_original,
    width='content',
    num_rows="dynamic",
    column_config={
        "cidade":         st.column_config.TextColumn("Cidade"),
        "qualidade_vida": st.column_config.NumberColumn("Q.V.", min_value=0, max_value=5),
        "lazer":          st.column_config.NumberColumn("Lazer", min_value=0, max_value=5),
        "natureza":       st.column_config.NumberColumn("Natureza", min_value=0, max_value=5),
        "custo":          st.column_config.NumberColumn("Custo", min_value=0, max_value=5),
        "seguranca":      st.column_config.NumberColumn("Segurança", min_value=0, max_value=5),
        "descricao":      st.column_config.TextColumn("Descrição"),
    },
    hide_index=True,
    key="tabela_cidades",
)

# ── Ranking Logic ─────────────────────────────────────────────────────────────
if calcular:
    importances = {
        "qualidade_vida": w_qv,
        "lazer": w_lazer,
        "natureza": w_nat,
        "custo": w_custo,
        "seguranca": w_seg,
        "proximidade": w_dist,
    }
   
    total_importance = sum(importances.values())
    
    # Métricas que serão normalizadas (excluindo proximidade)
    metrics = ["qualidade_vida", "lazer", "natureza", "custo", "seguranca"]
    
    # Calcula min e max uma única vez
    stats = edited_df[metrics].agg(['min', 'max'])
    
    def get_rank(row):
        # --- Proximidade ---
        ref_key = normalize_text(cidade_referencia)
        target_key = normalize_text(row['cidade'])
        
        try:
            dist = df_dist.loc[ref_key, target_key]
        except KeyError:
            dist = MAX_DISTANCE
            
        score_proximidade = max(0, (1 - (dist / MAX_DISTANCE)) * 10)

        # --- Normalização Min-Max para cada métrica ---
        weighted_sum = 0.0
        
        for m in metrics:
            val = row[m]
            min_val = stats.loc['min', m]
            max_val = stats.loc['max', m]
            
            if max_val == min_val:
                norm_value = 5.0
            else:
                norm_value = 10 * (val - min_val) / (max_val - min_val)
            
            weighted_sum += norm_value * importances[m]
        
        # Adiciona proximidade
        weighted_sum += score_proximidade * importances['proximidade']
        
        final_score = weighted_sum / total_importance
        
        return round(final_score, 2), dist

    # --- Aplicação e ordenação ---
    result_df = edited_df.copy()
    
    # Aplica a função e desempacota os resultados
    result_df[['score', 'distancia_real']] = result_df.apply(
        lambda row: pd.Series(get_rank(row)), axis=1
    )
    
    # Ordena e adiciona ranking
    result_df = result_df.sort_values("score", ascending=False).reset_index(drop=True)
    result_df.insert(0, "rank", result_df.index + 1)
    importances = {
        "qualidade_vida": w_qv,
        "lazer":          w_lazer,
        "natureza":       w_nat,
        "custo":          w_custo,
        "seguranca":      w_seg,
        "proximidade":    w_dist,
    }
    
    total_importance = sum(importances.values())

    def get_rank(row):
        ref_key = normalize_text(cidade_referencia)
        target_key = normalize_text(row['cidade'])
        try:
            dist = df_dist.loc[ref_key, target_key]
        except KeyError:
            dist = MAX_DISTANCE 

        score_proximidade = max(0, (1 - (dist / MAX_DISTANCE)) * 10)
        
        weighted_sum = (
            (row['qualidade_vida'] * importances['qualidade_vida']) +
            (row['lazer'] * importances['lazer']) +
            (row['natureza'] * importances['natureza']) +
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
    
    # Anchor point for scrolling
    st.markdown('<div id="ranking-result"></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div style="text-align:center; font-weight:bold; font-size:1.5rem; margin-bottom:1rem;">🏆 Ranking final (Referência: {cidade_referencia})</div>', unsafe_allow_html=True)

    st.dataframe(
        result_df,
        width='content',
        hide_index=True,
        column_config={
            "rank":           st.column_config.NumberColumn("#", width="small"),
            "cidade":         st.column_config.TextColumn("Cidade"),
            "score":          st.column_config.ProgressColumn("Score Total", min_value=0, max_value=5, format="%.2f"),
            "distancia_real": st.column_config.NumberColumn(f"Dist. de {cidade_referencia}(km)"),
            "qualidade_vida": st.column_config.NumberColumn("Q.V."),
            "lazer":          st.column_config.NumberColumn("Lazer"),
            "natureza":       st.column_config.NumberColumn("Nat."),
            "custo":          st.column_config.NumberColumn("Custo"),
            "seguranca":      st.column_config.NumberColumn("Seg."),
        },
    )

    if len(result_df) > 0:
        top = result_df.iloc[0]
        st.success(f"🥇 A melhor opção no seu caso é: **{top['cidade']}**")
    else:
        st.warning("Adicione mais cidades para ver o ranking.")

    # trigger the scroll
    components.html(
        """
        <script>
            window.parent.document.getElementById('ranking-result').scrollIntoView({behavior: 'smooth'});
        </script>
        """,
        height=0,
    )