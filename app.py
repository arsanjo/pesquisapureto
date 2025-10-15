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

def save_response_to_sheet(row_dict):
    _, ws = get_sheet_handles()
    if ws is None:
        # silencioso, segue a vida, mas avisa
        st.warning("⚠️ Não foi possível salvar na planilha agora. A conexão com o Google Sheets não está ativa.")
        return False
    headers = [
        "Data","Nome","Whatsapp","Aniversario","Como_Conheceu","Segmento",
        "Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente",
        "Nota_Pedido_Embalagem","NPS_Recomendacao","Comentario"
    ]
    values = [row_dict.get(h, "") for h in headers]
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
    st.session_state.respostas = pd.DataFrame(columns=[
        "Data","Nome","Whatsapp","Aniversario","Como_Conheceu","Segmento",
        "Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente",
        "Nota_Pedido_Embalagem","NPS_Recomendacao","Comentario"
    ])
if 'aniversario_raw_value' not in st.session_state:
    st.session_state.aniversario_raw_value = ""
if 'como_outro_input_value' not in st.session_state:
    st.session_state.como_outro_input_value = ""
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'ultimo_nps' not in st.session_state:
    st.session_state.ultimo_nps = 0
if 'ultimo_nome' not in st.session_state:
    st.session_state.ultimo_nome = ""

# ==============================
# ROTEAMENTO (ADMIN vs PÚBLICO)
# ==============================
query = st.query_params
admin_mode = (ADMIN_KEY in query and query[ADMIN_KEY] == ADMIN_PASSWORD)

# ==============================
# DASHBOARD ADMIN
# ==============================
if admin_mode:
    st.markdown("## 🔐 Dashboard Administrativo — Pureto Sushi")

    df = load_responses_from_sheet()
    if df.empty:
        st.warning("Ainda não há respostas coletadas.")
        st.stop()

    notas_cols = ["Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente",
                  "Nota_Pedido_Embalagem","NPS_Recomendacao"]
    for c in notas_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df_salao = df[df["Segmento"] == "Restaurante (Salão)"]
    df_delivery = df[df["Segmento"] == "Delivery (Entrega)"]

    nps_geral, prom_g, neut_g, det_g, total = calcular_nps(df)
    nps_salao, *_ = calcular_nps(df_salao)
    nps_delivery, *_ = calcular_nps(df_delivery)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Respostas", f"{total}")
    col2.metric("NPS Geral", f"{nps_geral:.1f}")
    col3.metric("Total Salão", f"{len(df_salao)}")
    col4.metric("Total Delivery", f"{len(df_delivery)}")

    st.markdown("---")

    # NPS por experiência
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

    # Médias por critério - Salão
    st.markdown("### 🍽️ Médias por Critério - Restaurante (Salão)")
    if not df_salao.empty:
        medias_salao = df_salao[["Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente"]].mean()
        df_med_salao = pd.DataFrame({"Critério": medias_salao.index, "Média": medias_salao.values})
        graf_salao = alt.Chart(df_med_salao).mark_bar().encode(
            x=alt.X("Critério:N", title=""),
            y=alt.Y("Média:Q", scale=alt.Scale(domain=[0,10])),
            tooltip=["Critério","Média"]
        )
        st.altair_chart(graf_salao, use_container_width=True)
    else:
        st.info("Nenhuma resposta de salão até o momento.")

    # Médias por critério - Delivery
    st.markdown("### 🛵 Médias por Critério - Delivery (Entrega)")
    if not df_delivery.empty:
        medias_del = df_delivery[["Nota_Atendimento","Nota_Pedido_Embalagem","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente"]].mean()
        df_med_del = pd.DataFrame({"Critério": medias_del.index, "Média": medias_del.values})
        graf_del = alt.Chart(df_med_del).mark_bar().encode(
            x=alt.X("Critério:N", title=""),
            y=alt.Y("Média:Q", scale=alt.Scale(domain=[0,10])),
            tooltip=["Critério","Média"]
        )
        st.altair_chart(graf_del, use_container_width=True)
    else:
        st.info("Nenhuma resposta de delivery até o momento.")

    # Evolução do NPS ao longo do tempo
    st.markdown("### ⏱️ Evolução do NPS ao Longo do Tempo")
    df['Data_Convertida'] = pd.to_datetime(df['Data'], errors='coerce', format='%d/%m/%Y %H:%M')
    nps_time = df.groupby(df['Data_Convertida'].dt.date)['NPS_Recomendacao'].mean().reset_index()
    nps_time.rename(columns={'NPS_Recomendacao': 'NPS_Médio'}, inplace=True)
    if not nps_time.empty:
        line = (
            alt.Chart(nps_time)
            .mark_line(point=True)
            .encode(
                x="Data_Convertida:T",
                y="NPS_Médio:Q",
                tooltip=["Data_Convertida:T","NPS_Médio:Q"]
            )
            .properties(height=250)
        )
        st.altair_chart(line, use_container_width=True)

    # Como nos conheceu
    st.markdown("### 📣 Como nos conheceu — Canais de aquisição")
    canais = df["Como_Conheceu"].value_counts().reset_index()
    canais.columns = ["Canal", "Quantidade"]
    canais = canais.sort_values(by="Quantidade", ascending=False)
    if not canais.empty:
        chart_canais = alt.Chart(canais).mark_bar().encode(
            y=alt.Y("Canal:N", sort='-x', title=""),
            x=alt.X("Quantidade:Q", title="Quantidade"),
            tooltip=["Canal:N","Quantidade:Q"]
        ).properties(height=320)
        st.altair_chart(chart_canais, use_container_width=True)

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
                if col in d and not pd.isna(d[col]):
                    st.markdown(f"- {col.replace('_',' ')}: **{d[col]}**")
            if d.get("Comentario", ""):
                st.markdown(f"#### 💬 Comentário:\n> {d['Comentario']}")

    with st.expander("💬 Ver comentários de todos os clientes"):
        for _, row in df[df["Comentario"].notna() & (df["Comentario"] != "")].iterrows():
            st.markdown(f"**{row['Nome']}** ({row['Segmento']}) — {row['Data']}")
            st.markdown(f"⭐️ NPS: {row['NPS_Recomendacao']} 🗣️ {row['Comentario']}")
            st.markdown("---")

    csv = to_csv_bytes(df)
    st.download_button("📥 Baixar Respostas (CSV)", csv, "respostas_pureto.csv", "text/csv")

# ==============================
# MODO PÚBLICO (FORMULÁRIO + SUCESSO)
# ==============================
else:
    if not st.session_state.submitted:
        # Título
        st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40 segundos.</p>", unsafe_allow_html=True)
        st.markdown("---")

        segmento = st.radio("**Sua compra na Pureto foi?**",
                            ["Restaurante (Salão)", "Delivery (Entrega)"],
                            horizontal=True, key="segmento_selecionado")
        st.markdown("---")

        # Opções de "Como nos conheceu"
        if segmento == "Restaurante (Salão)":
            opcoes_conheceu = [
                "Selecione uma opção","Já era cliente do delivery","Instagram","Facebook","Google",
                "Indicação de amigo/familiar","Passando em frente ao restaurante","Placa na entrada de Schroeder (ponte)","Outro:"
            ]
        else:
            opcoes_conheceu = [
                "Selecione uma opção","Já era cliente do salão","Instagram","Facebook","Google",
                "Indicação de amigo/familiar","Passando em frente ao restaurante","Placa na entrada de Schroeder (ponte)","Outro:"
            ]

        como_conheceu = st.selectbox("Como nos conheceu?", opcoes_conheceu, key="conheceu_select")

        como_outro = ""
        if como_conheceu == "Outro:":
            como_outro = st.text_input("Como nos conheceu? (Especifique):",
                                       value=st.session_state.como_outro_input_value,
                                       key="como_outro_input")
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

            st.markdown(f"**Como nos conheceu:** {como_conheceu}{f' (Especificado: {como_outro})' if como_outro else ''}")
            st.markdown("---")

            opcoes = list(range(0, 11))
            nota_atend, nota_sabor, nota_ambiente, nota_embalagem, nps = 0, 0, 0, None, 0

            if segmento == "Restaurante (Salão)":
                st.subheader("🍽️ Avaliação do Salão")
                nota_atend = st.radio("1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):", opcoes, horizontal=True, key="nota_atendimento_s")
                nota_sabor = st.radio("2️⃣ Qualidade e sabor dos pratos:", opcoes, horizontal=True, key="nota_sabor_s")
                nota_ambiente = st.radio("3️⃣ Ambiente e limpeza:", opcoes, horizontal=True, key="nota_ambiente_s")
                nota_embalagem = None
                nps = st.radio("4️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria?", opcoes, horizontal=True, key="nps_s")
            else:
                st.subheader("🛵 Avaliação do Delivery")
                nota_atend = st.radio("1️⃣ Atendimento e facilidade do pedido:", opcoes, horizontal=True, key="nota_atendimento_d")
                nota_embalagem = st.radio("2️⃣ Logística (tempo e embalagem):", opcoes, horizontal=True, key="nota_embalagem_d")
                nota_sabor = st.radio("3️⃣ Qualidade e sabor pós-entrega:", opcoes, horizontal=True, key="nota_sabor_d")
                nota_ambiente = st.radio("4️⃣ Apresentação e cuidado com os itens:", opcoes, horizontal=True, key="nota_ambiente_d")
                nps = st.radio("5️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria?", opcoes, horizontal=True, key="nps_d")

            comentario = st.text_area("💬 Comentários, sugestões, elogios ou reclamações (opcional):", max_chars=500, key="comentario_input_form")
            submit = st.form_submit_button("Enviar Respostas ✅")

        if submit:
            if not nome or not whatsapp or como_conheceu == "Selecione uma opção":
                st.error("⚠️ Por favor, preencha Nome, WhatsApp e Como nos conheceu.")
            elif aniversario and (len("".join(c for c in st.session_state.aniversario_raw_value if c.isdigit())) != 8):
                st.error("⚠️ Data de aniversário inválida. Por favor, use 8 dígitos (DDMMAAAA).")
            else:
                como_conheceu_final = como_outro if como_conheceu == "Outro:" else como_conheceu
                nova = {
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Nome": nome,
                    "Whatsapp": whatsapp,
                    "Aniversario": aniversario,
                    "Como_Conheceu": como_conheceu_final,
                    "Segmento": segmento,
                    "Nota_Atendimento": nota_atend,
                    "Nota_Qualidade_Sabor": nota_sabor,
                    "Nota_Entrega_Ambiente": nota_ambiente,
                    "Nota_Pedido_Embalagem": nota_embalagem if nota_embalagem is not None else "",
                    "NPS_Recomendacao": nps,
                    "Comentario": comentario
                }

                # salva local (para a tela de sucesso)
                st.session_state.respostas = pd.concat([st.session_state.respostas, pd.DataFrame([nova])], ignore_index=True)
                # salva persistente
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
