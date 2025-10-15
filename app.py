import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# ==============================
# CONFIGURAÇÕES
# ==============================
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"
INSTAGRAM_LINK = "https://www.instagram.com/puretosushi"
ADMIN_KEY = "admin"
ADMIN_PASSWORD = "pureto2025"

# ==============================
# FUNÇÕES AUXILIARES
# ==============================
def calcular_nps(df):
    if df.empty or "NPS_Recomendacao" not in df.columns:
        return 0.0, 0.0, 0.0, 0.0, 0
    total = len(df)
    promotores = (pd.to_numeric(df["NPS_Recomendacao"], errors="coerce").fillna(0) >= 9).sum()
    detratores = (pd.to_numeric(df["NPS_Recomendacao"], errors="coerce").fillna(0) <= 6).sum()
    perc_prom = promotores / total * 100 if total else 0
    perc_det = detratores / total * 100 if total else 0
    perc_neut = 100 - perc_prom - perc_det
    nps = perc_prom - perc_det
    return nps, perc_prom, perc_neut, perc_det, total

@st.cache_data
def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

# ==============================
# CONEXÃO COM GOOGLE SHEETS
# ==============================
@st.cache_resource(show_spinner=False)
def get_sheet_handles():
    try:
        from google.oauth2.service_account import Credentials
        import gspread

        secrets = st.secrets.get("gcp_service_account", None)
        sheet_url = st.secrets.get("google_sheet", {}).get("sheet_url", "")
        if not secrets or not sheet_url:
            return None, None

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(dict(secrets), scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_url(sheet_url)
        ws = sh.sheet1
        return client, ws
    except Exception:
        return None, None

def load_responses_from_sheet():
    _, ws = get_sheet_handles()
    headers = [
        "Data","Nome","Whatsapp","Aniversario","Como_Conheceu","Segmento",
        "Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente",
        "Nota_Pedido_Embalagem","NPS_Recomendacao","Comentario"
    ]
    if ws is None:
        return pd.DataFrame(columns=headers)
    try:
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        for h in headers:
            if h not in df.columns:
                df[h] = []
        return df[headers]
    except Exception:
        return pd.DataFrame(columns=headers)

# ==============================
# MODO ADMIN
# ==============================
query = st.query_params
admin_mode = (ADMIN_KEY in query and query[ADMIN_KEY] == ADMIN_PASSWORD)

if admin_mode:
    st.markdown("## 🔐 Dashboard Administrativo — Pureto Sushi")

    df = load_responses_from_sheet()
    if df.empty:
        st.warning("Ainda não há respostas coletadas.")
        st.stop()

    # CONVERSÃO DE TIPOS
    notas_cols = ["Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente",
                  "Nota_Pedido_Embalagem","NPS_Recomendacao"]
    for c in notas_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # SUBSETS
    df_salao = df[df["Segmento"] == "Restaurante (Salão)"]
    df_delivery = df[df["Segmento"] == "Delivery (Entrega)"]

    # NPS
    nps_geral, prom_g, neut_g, det_g, total = calcular_nps(df)
    nps_salao, *_ = calcular_nps(df_salao)
    nps_delivery, *_ = calcular_nps(df_delivery)

    # ==============================
    # RESUMO GERAL
    # ==============================
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Respostas", f"{total}")
    col2.metric("NPS Geral", f"{nps_geral:.1f}")
    col3.metric("Total Salão", f"{len(df_salao)}")
    col4.metric("Total Delivery", f"{len(df_delivery)}")

    st.markdown("---")

    # ==============================
    # NPS POR EXPERIÊNCIA
    # ==============================
    st.markdown("### 📈 NPS por Experiência")
    nps_df = pd.DataFrame({
        "Categoria": ["Geral", "Salão", "Delivery"],
        "NPS": [nps_geral, nps_salao, nps_delivery]
    })
    bar = (
        alt.Chart(nps_df)
        .mark_bar(size=80)
        .encode(
            x=alt.X("Categoria:N", title=""),
            y=alt.Y("NPS:Q", scale=alt.Scale(domain=[-100, 100])),
            tooltip=["Categoria:N","NPS:Q"]
        )
        .properties(height=220)
    )
    labels = alt.Chart(nps_df).mark_text(dy=-10).encode(x="Categoria:N", y="NPS:Q", text=alt.Text("NPS:Q"))
    st.altair_chart(bar + labels, use_container_width=True)
    st.caption("🟢 Promotores (9–10) | 🟡 Neutros (7–8) | 🔴 Detratores (0–6)")

    # ==============================
    # MÉDIAS POR CRITÉRIO
    # ==============================
    st.markdown("### 🍽️ Médias por Critério - Restaurante (Salão)")
    if not df_salao.empty:
        medias_salao = df_salao[["Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente"]].mean()
        df_med_salao = pd.DataFrame({"Critério": medias_salao.index, "Média": medias_salao.values})
        graf_salao = (
            alt.Chart(df_med_salao)
            .mark_bar()
            .encode(x=alt.X("Critério:N", title=""), y=alt.Y("Média:Q", scale=alt.Scale(domain=[0,10])), tooltip=["Critério","Média"])
        )
        st.altair_chart(graf_salao, use_container_width=True)
    else:
        st.info("Nenhuma resposta de salão até o momento.")

    st.markdown("### 🛵 Médias por Critério - Delivery (Entrega)")
    if not df_delivery.empty:
        medias_del = df_delivery[["Nota_Atendimento","Nota_Pedido_Embalagem","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente"]].mean()
        df_med_del = pd.DataFrame({"Critério": medias_del.index, "Média": medias_del.values})
        graf_del = (
            alt.Chart(df_med_del)
            .mark_bar()
            .encode(x=alt.X("Critério:N", title=""), y=alt.Y("Média:Q", scale=alt.Scale(domain=[0,10])), tooltip=["Critério","Média"])
        )
        st.altair_chart(graf_del, use_container_width=True)
    else:
        st.info("Nenhuma resposta de delivery até o momento.")

    # ==============================
    # EVOLUÇÃO DO NPS
    # ==============================
    st.markdown("### ⏱️ Evolução do NPS ao Longo do Tempo")
    df['Data_Convertida'] = pd.to_datetime(df['Data'], errors='coerce', format='%d/%m/%Y %H:%M')
    nps_time = df.groupby(df['Data_Convertida'].dt.date)['NPS_Recomendacao'].mean().reset_index()
    nps_time.rename(columns={'NPS_Recomendacao': 'NPS_Médio'}, inplace=True)
    if not nps_time.empty:
        line = (
            alt.Chart(nps_time)
            .mark_line(point=True)
            .encode(x="Data_Convertida:T", y="NPS_Médio:Q", tooltip=["Data_Convertida:T","NPS_Médio:Q"])
            .properties(height=250)
        )
        st.altair_chart(line, use_container_width=True)
    else:
        st.info("Ainda não há dados suficientes para o gráfico de evolução.")

    # ==============================
    # COMO NOS CONHECEU
    # ==============================
    st.markdown("### 📣 Como nos conheceu — Canais de aquisição")
    canais = df["Como_Conheceu"].value_counts().reset_index()
    canais.columns = ["Canal", "Quantidade"]
    canais = canais.sort_values(by="Quantidade", ascending=False)
    if not canais.empty:
        chart_canais = (
            alt.Chart(canais)
            .mark_bar()
            .encode(
                y=alt.Y("Canal:N", sort='-x', title=""),
                x=alt.X("Quantidade:Q", title="Quantidade"),
                tooltip=["Canal:N","Quantidade:Q"]
            )
            .properties(height=320)
        )
        st.altair_chart(chart_canais, use_container_width=True)
    else:
        st.info("Nenhum dado disponível sobre 'Como nos conheceu'.")

    # ==============================
    # FILTRO INDIVIDUAL DE CLIENTE
    # ==============================
    st.markdown("---")
    st.markdown("### 👤 Ver respostas individuais")
    clientes = sorted(df["Nome"].dropna().unique())
    if clientes:
        selecionado = st.selectbox("Selecione um cliente:", clientes)
        dados = df[df["Nome"] == selecionado]
        if not dados.empty:
            d = dados.iloc[-1]
            st.markdown(f"**Data:** {d['Data']}")
            st.markdown(f"**Segmento:** {d['Segmento']}")
            st.markdown(f"**NPS:** {d['NPS_Recomendacao']}")
            st.markdown("#### Notas:")
            for col in ["Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente","Nota_Pedido_Embalagem"]:
                if not pd.isna(d[col]):
                    st.markdown(f"- {col.replace('_',' ')}: **{d[col]}**")
            if d["Comentario"]:
                st.markdown(f"#### 💬 Comentário:\n> {d['Comentario']}")
    else:
        st.info("Nenhum cliente respondeu ainda.")

    # ==============================
    # EXPANSOR DE COMENTÁRIOS
    # ==============================
    st.markdown("---")
    with st.expander("💬 Ver comentários de todos os clientes"):
        for _, row in df[df["Comentario"].notna() & (df["Comentario"] != "")].iterrows():
            st.markdown(f"**{row['Nome']}** ({row['Segmento']}) — {row['Data']}")
            st.markdown(f"⭐️ NPS: {row['NPS_Recomendacao']} 🗣️ {row['Comentario']}")
            st.markdown("---")

    # DOWNLOAD CSV
    st.markdown("---")
    csv = to_csv_bytes(df)
    st.download_button("📥 Baixar Respostas (CSV)", csv, "respostas_pureto.csv", "text/csv")

