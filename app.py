import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# ==============================
# CONFIGURAÇÕES
# ==============================
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Delivery", layout="wide")

GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"
INSTAGRAM_LINK = "https://www.instagram.com/puretosushi"
ADMIN_KEY = "admin"
ADMIN_PASSWORD = "pureto2025"

SEGMENTO_FIXO = "Delivery (Entrega)"  # agora é sempre delivery

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

HEADERS = [
    "Data","Nome","Whatsapp","Aniversario","Como_Conheceu","Segmento",
    "Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente",
    "Nota_Pedido_Embalagem","NPS_Recomendacao","Comentario"
]

def load_responses_from_sheet():
    _, ws = get_sheet_handles()
    if ws is None:
        return pd.DataFrame(columns=HEADERS)
    try:
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        for h in HEADERS:
            if h not in df.columns:
                df[h] = ""
        return df[HEADERS]
    except Exception:
        return pd.DataFrame(columns=HEADERS)

def save_response_to_sheet(row_dict):
    _, ws = get_sheet_handles()
    if ws is None:
        st.warning("⚠️ Não foi possível salvar na planilha agora. A conexão com o Google Sheets não está ativa.")
        return False
    values = [row_dict.get(h, "") for h in HEADERS]
    try:
        ws.append_row(values, value_input_option="USER_ENTERED")
        return True
    except Exception:
        st.warning("⚠️ Ocorreu um problema ao gravar na planilha. Tente novamente em instantes.")
        return False

# ==============================
# ESTADO
# ==============================
if "respostas" not in st.session_state:
    st.session_state.respostas = pd.DataFrame(columns=HEADERS)
if "aniversario_raw_value" not in st.session_state:
    st.session_state.aniversario_raw_value = ""
if "como_outro_input_value" not in st.session_state:
    st.session_state.como_outro_input_value = ""
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "ultimo_nps" not in st.session_state:
    st.session_state.ultimo_nps = 0
if "ultimo_nome" not in st.session_state:
    st.session_state.ultimo_nome = ""

# ==============================
# ROTEAMENTO (ADMIN vs PÚBLICO)
# ==============================
query = st.query_params
admin_mode = (ADMIN_KEY in query and query[ADMIN_KEY] == ADMIN_PASSWORD)

# ==============================
# DASHBOARD ADMIN (DELIVERY INTELIGENTE)
# ==============================
if admin_mode:
    st.markdown("## 🔐 Dashboard Administrativo — Pureto Delivery")

    df = load_responses_from_sheet()
    if df.empty:
        st.warning("Ainda não há respostas coletadas.")
        st.stop()

    # Converte notas
    notas_cols = [
        "Nota_Atendimento",
        "Nota_Pedido_Embalagem",
        "Nota_Entrega_Ambiente",
        "Nota_Qualidade_Sabor",
        "NPS_Recomendacao"
    ]
    for c in notas_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Converte data
    df["Data_Convertida"] = pd.to_datetime(df["Data"], errors="coerce", format="%d/%m/%Y %H:%M")

    # Filtra só delivery (compatível com dados antigos)
    df_delivery = df[df["Segmento"].fillna("").isin(["Delivery (Entrega)", "Delivery", "", "Entrega"])].copy()
    if df_delivery.empty:
        df_delivery = df.copy()

    # ---------- FILTROS ----------
    st.markdown("### 🎛️ Filtros")
    colf1, colf2, colf3 = st.columns([1, 1, 2])

    min_dt = df_delivery["Data_Convertida"].min()
    max_dt = df_delivery["Data_Convertida"].max()

    if pd.isna(min_dt) or pd.isna(max_dt):
        st.warning("Não foi possível interpretar as datas. Verifique o formato da coluna 'Data'.")
        df_filtrado = df_delivery.copy()
    else:
        data_ini = colf1.date_input("Data inicial", value=min_dt.date())
        data_fim = colf2.date_input("Data final", value=max_dt.date())

        canais_unicos = sorted([
            c for c in df_delivery["Como_Conheceu"].dropna().unique().tolist()
            if str(c).strip() != ""
        ])
        canal = colf3.selectbox("Canal (Como nos conheceu)", ["Todos"] + canais_unicos)

        df_filtrado = df_delivery.copy()
        df_filtrado = df_filtrado[df_filtrado["Data_Convertida"].dt.date >= data_ini]
        df_filtrado = df_filtrado[df_filtrado["Data_Convertida"].dt.date <= data_fim]
        if canal != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Como_Conheceu"] == canal]

    if df_filtrado.empty:
        st.info("Sem dados para os filtros selecionados.")
        st.stop()

    # ---------- KPIs ----------
    st.markdown("---")
    st.markdown("### 📌 Resumo do período")

    nps_geral, prom_g, neut_g, det_g, total = calcular_nps(df_filtrado)

    media_atend = df_filtrado["Nota_Atendimento"].mean()
    media_tempo = df_filtrado["Nota_Pedido_Embalagem"].mean()      # Tempo de entrega
    media_emb = df_filtrado["Nota_Entrega_Ambiente"].mean()        # Embalagem/conservação
    media_prod = df_filtrado["Nota_Qualidade_Sabor"].mean()        # Produto

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Respostas", f"{total}")
    c2.metric("NPS", f"{nps_geral:.1f}")
    c3.metric("Promotores", f"{prom_g:.1f}%")
    c4.metric("Neutros", f"{neut_g:.1f}%")
    c5.metric("Detratores", f"{det_g:.1f}%")

    st.markdown("### ⭐ Médias por Pilar (0–10)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Pedido + Atendimento", f"{media_atend:.2f}")
    k2.metric("Tempo de Entrega", f"{media_tempo:.2f}")
    k3.metric("Embalagem + Conservação", f"{media_emb:.2f}")
    k4.metric("Qualidade do Produto", f"{media_prod:.2f}")

    # ---------- % notas baixas por pilar ----------
    def perc_baixa(serie):
        s = pd.to_numeric(serie, errors="coerce").dropna()
        if len(s) == 0:
            return 0.0
        return (s <= 6).sum() / len(s) * 100

    st.markdown("### 🚨 % de notas baixas (0–6) por pilar")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Pedido + Atendimento", f"{perc_baixa(df_filtrado['Nota_Atendimento']):.1f}%")
    b2.metric("Tempo de Entrega", f"{perc_baixa(df_filtrado['Nota_Pedido_Embalagem']):.1f}%")
    b3.metric("Embalagem + Conservação", f"{perc_baixa(df_filtrado['Nota_Entrega_Ambiente']):.1f}%")
    b4.metric("Qualidade do Produto", f"{perc_baixa(df_filtrado['Nota_Qualidade_Sabor']):.1f}%")

    st.markdown("---")

    # ---------- GRÁFICO: médias por pilar ----------
    st.markdown("### 📊 Médias por Pilar — Gráfico")
    df_med = pd.DataFrame({
        "Pilar": ["Pedido + Atendimento", "Tempo de Entrega", "Embalagem + Conservação", "Qualidade do Produto"],
        "Média": [media_atend, media_tempo, media_emb, media_prod]
    })
    graf = alt.Chart(df_med).mark_bar().encode(
        x=alt.X("Pilar:N", title=""),
        y=alt.Y("Média:Q", scale=alt.Scale(domain=[0, 10])),
        tooltip=["Pilar:N", "Média:Q"]
    ).properties(height=260)
    st.altair_chart(graf, use_container_width=True)

    # ---------- EVOLUÇÃO NPS ----------
    st.markdown("### ⏱️ Evolução do NPS (por dia)")
    tmp = df_filtrado.dropna(subset=["Data_Convertida"]).copy()
    tmp["Dia"] = tmp["Data_Convertida"].dt.date
    nps_time = tmp.groupby("Dia")["NPS_Recomendacao"].mean().reset_index()
    line = alt.Chart(nps_time).mark_line(point=True).encode(
        x=alt.X("Dia:T", title=""),
        y=alt.Y("NPS_Recomendacao:Q", title="NPS médio"),
        tooltip=["Dia:T", "NPS_Recomendacao:Q"]
    ).properties(height=260)
    st.altair_chart(line, use_container_width=True)

    # ---------- CANAIS ----------
    st.markdown("### 📣 Canais (Como nos conheceu)")
    canais = df_filtrado["Como_Conheceu"].fillna("").value_counts().reset_index()
    canais.columns = ["Canal", "Quantidade"]
    canais = canais[canais["Canal"] != ""]
    if not canais.empty:
        chart_canais = alt.Chart(canais).mark_bar().encode(
            y=alt.Y("Canal:N", sort="-x", title=""),
            x=alt.X("Quantidade:Q", title="Quantidade"),
            tooltip=["Canal:N", "Quantidade:Q"]
        ).properties(height=320)
        st.altair_chart(chart_canais, use_container_width=True)

    st.markdown("### 🧠 NPS por canal (top 10 em volume)")
    tmp2 = df_filtrado[df_filtrado["Como_Conheceu"].fillna("").str.strip() != ""].copy()
    base = tmp2.groupby("Como_Conheceu").agg(
        Respostas=("NPS_Recomendacao", "count"),
        NPS_Medio=("NPS_Recomendacao", "mean")
    ).reset_index().sort_values("Respostas", ascending=False).head(10)

    if not base.empty:
        chart_nps_canal = alt.Chart(base).mark_bar().encode(
            y=alt.Y("Como_Conheceu:N", sort="-x", title=""),
            x=alt.X("NPS_Medio:Q", title="NPS médio"),
            tooltip=["Como_Conheceu:N", "Respostas:Q", "NPS_Medio:Q"]
        ).properties(height=320)
        st.altair_chart(chart_nps_canal, use_container_width=True)

    # ---------- LISTAS: detratores e neutros ----------
    st.markdown("---")
    st.markdown("### 🧯 Recuperação de clientes (prioridade)")
    colr1, colr2 = st.columns(2)

    detratores = df_filtrado[pd.to_numeric(df_filtrado["NPS_Recomendacao"], errors="coerce") <= 6].copy()
    neutros = df_filtrado[pd.to_numeric(df_filtrado["NPS_Recomendacao"], errors="coerce").between(7, 8)].copy()

    with colr1:
        st.markdown("#### 🔴 Detratores (NPS 0–6)")
        if detratores.empty:
            st.info("Nenhum detrator no período.")
        else:
            show_det = detratores[["Data", "Nome", "Whatsapp", "NPS_Recomendacao", "Comentario"]].sort_values("Data", ascending=False)
            st.dataframe(show_det, use_container_width=True, hide_index=True)

    with colr2:
        st.markdown("#### 🟡 Neutros (NPS 7–8)")
        if neutros.empty:
            st.info("Nenhum neutro no período.")
        else:
            show_neu = neutros[["Data", "Nome", "Whatsapp", "NPS_Recomendacao", "Comentario"]].sort_values("Data", ascending=False)
            st.dataframe(show_neu, use_container_width=True, hide_index=True)

    # ---------- EXPORT ----------
    st.markdown("---")
    csv = to_csv_bytes(df_filtrado.drop(columns=["Data_Convertida"], errors="ignore"))
    st.download_button("📥 Baixar dados filtrados (CSV)", csv, "respostas_pureto_delivery_filtrado.csv", "text/csv")


# ==============================
# MODO PÚBLICO (FORMULÁRIO + SUCESSO) — DELIVERY ONLY
# ==============================
else:
    if not st.session_state.submitted:
        st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40 segundos.</p>", unsafe_allow_html=True)
        st.markdown("---")

        # Como nos conheceu (Delivery)
        opcoes_conheceu = [
            "Selecione uma opção",
            "Indicação de amigo/familiar",
            "Instagram",
            "Facebook",
            "Google",
            "Ifood",
            "Placa na entrada de Schroeder (ponte)",
            "Placa pela cidade",
            "Outro:"
        ]

        como_conheceu = st.selectbox("Como nos conheceu?", opcoes_conheceu, key="conheceu_select")

        if como_conheceu == "Outro:":
            como_outro = st.text_input(
                "Como nos conheceu? (Especifique):",
                value=st.session_state.como_outro_input_value,
                key="como_outro_input"
            )
            st.session_state.como_outro_input_value = como_outro
        else:
            como_outro = ""

        with st.form("pesquisa_form"):
            st.subheader("Sobre você")
            col1, col2, col3 = st.columns(3)

            nome = col1.text_input("Seu nome completo:", key="nome_input_form")
            whatsapp = col2.text_input("Seu WhatsApp:", key="whatsapp_input_form")

            aniversario_raw = col3.text_input(
                "Data de aniversário (DD/MM/AAAA):",
                value=st.session_state.aniversario_raw_value,
                placeholder="Ex: 14101972 (apenas números)",
                key="aniversario_raw_input"
            )
            st.session_state.aniversario_raw_value = aniversario_raw
            aniversario = "".join(c for c in aniversario_raw if c.isdigit())
            if len(aniversario) == 8:
                aniversario = f"{aniversario[:2]}/{aniversario[2:4]}/{aniversario[4:]}"

            st.markdown("---")

            # Avaliação Delivery (0-10)
            st.subheader("🛵 Avaliação do Delivery")
            opcoes = list(range(0, 11))

            st.markdown("**1️⃣ Pedido e Atendimento**")
            st.caption("(Site, WhatsApp ou iFood)")
            nota_atend = st.radio("", opcoes, horizontal=True, key="nota_atendimento_d")

            st.markdown("**2️⃣ Tempo de Entrega**")
            st.caption("(Sua satisfação com o tempo de entrega)")
            nota_tempo = st.radio("", opcoes, horizontal=True, key="nota_tempo_d")

            st.markdown("**3️⃣ Embalagem e Conservação**")
            st.caption("(Organização e temperatura)")
            nota_embalagem = st.radio("", opcoes, horizontal=True, key="nota_embalagem_d")

            st.markdown("**4️⃣ Qualidade dos Produtos**")
            st.caption("(Sabor e aparência)")
            nota_produto = st.radio("", opcoes, horizontal=True, key="nota_produto_d")

            nps = st.radio(
                "5️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria?",
                opcoes, horizontal=True, key="nps_d"
            )

            comentario = st.text_area(
                "💬 Teve algo que poderíamos melhorar ou que superou sua expectativa? (Opcional)",
                max_chars=500, key="comentario_input_form"
            )

            submit = st.form_submit_button("Enviar Respostas ✅")

        if submit:
            if not nome or not whatsapp or como_conheceu == "Selecione uma opção":
                st.error("⚠️ Por favor, preencha Nome, WhatsApp e Como nos conheceu.")
            elif aniversario and (len("".join(c for c in st.session_state.aniversario_raw_value if c.isdigit())) != 8):
                st.error("⚠️ Data de aniversário inválida. Por favor, use 8 dígitos (DDMMAAAA).")
            else:
                como_conheceu_final = como_outro if como_conheceu == "Outro:" else como_conheceu

                # Mantém compatibilidade com sua planilha antiga:
                # - Nota_Atendimento = Pedido/Atendimento
                # - Nota_Pedido_Embalagem = Tempo de entrega
                # - Nota_Entrega_Ambiente = Embalagem/Conservação
                # - Nota_Qualidade_Sabor = Qualidade dos produtos
                nova = {
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Nome": nome,
                    "Whatsapp": whatsapp,
                    "Aniversario": aniversario,
                    "Como_Conheceu": como_conheceu_final,
                    "Segmento": SEGMENTO_FIXO,
                    "Nota_Atendimento": nota_atend,
                    "Nota_Pedido_Embalagem": nota_tempo,
                    "Nota_Entrega_Ambiente": nota_embalagem,
                    "Nota_Qualidade_Sabor": nota_produto,
                    "NPS_Recomendacao": nps,
                    "Comentario": comentario
                }

                st.session_state.respostas = pd.concat(
                    [st.session_state.respostas, pd.DataFrame([nova])],
                    ignore_index=True
                )
                save_response_to_sheet(nova)

                st.session_state.submitted = True
                st.session_state.ultimo_nome = nome
                st.session_state.ultimo_nps = nps
                st.rerun()

    else:
        # TELA DE SUCESSO
        nome_sucesso = st.session_state.ultimo_nome
        nps_sucesso = int(st.session_state.ultimo_nps)

        st.success("✅ Pesquisa enviada com sucesso!")
        st.markdown(f"""
        <div style='background-color:#e8f5e9; color:#1b5e20; padding:20px; border-radius:10px; margin-top:20px;'>
        <h3>🎉 {nome_sucesso}, muito obrigado pelas suas respostas sinceras!</h3>
        <p>Seu feedback é essencial para aperfeiçoarmos cada detalhe do <b>Pureto Sushi</b>.</p>
        <p>Como forma de agradecimento, você ganhou um <b>cupom especial de 10% de desconto</b> na sua próxima compra.</p>
        <p style='font-size:1.2em;'><b>Use o código:</b> <span style='color:#007bff;'>PESQUISA</span></p>
        </div>
        """, unsafe_allow_html=True)

        if nps_sucesso >= 9:
            st.balloons()
            st.markdown(f"""
            <div style='background-color:#fff3cd; color:#856404; padding:20px; border-radius:10px; margin-top:25px;'>
            <h4 style='font-weight:bold;'>Google <span style='font-size:1.5em;'>⭐⭐⭐⭐⭐</span></h4>
            <p>{nome_sucesso}, e que tal compartilhar sua opinião lá no Google? Isso nos ajuda muito! 🙏</p>
            <p><b>Como gratidão pela sua avaliação no Google, sua próxima entrega será grátis!</b></p>
            <a href='{GOOGLE_REVIEW_LINK}' target='_blank'
               style='background-color:#f0ad4e; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;'>
               💬 Avaliar no Google
            </a>
            </div>""", unsafe_allow_html=True)

        # CTA Instagram (sempre)
        st.markdown(f"""
        <div style='background-color:#f5f5f5; color:#222; padding:20px; border-radius:10px; margin-top:30px; text-align:center;'>
            <p style='font-size:1.1em;'>
                <img src="https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png" width="22" style="vertical-align:middle; margin-right:6px;">
                Siga a <b>Pureto Sushi</b> no Instagram:
                <a href="{INSTAGRAM_LINK}" target="_blank" style="color:#e1306c; text-decoration:none; font-weight:bold;">
                    @puretosushi
                </a>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # RODAPÉ (apenas na tela de sucesso)
        st.markdown("""
        <div style='text-align:center; font-size:0.9em; color:gray; margin-top:40px; line-height:1.6;'>
            <p style='margin-bottom:4px;'>
                Criado e desenvolvido por 
                <a href='https://wa.me/5547996008166' target='_blank' style='color:#007bff; text-decoration:none; font-weight:bold;'>
                    Arsanjo
                </a>
            </p>
            <p style='font-style:italic; color:#666; margin:0;'>
                “Tudo o que fizerem, façam de todo o coração, como para o Senhor.”<br>— Colossenses 3:23
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.info("Obrigado por contribuir!")
