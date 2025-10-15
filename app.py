import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# ============ CONFIGS ============
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"
INSTAGRAM_LINK = "https://www.instagram.com/puretosushi"
ADMIN_KEY = "admin"
ADMIN_PASSWORD = "pureto2025"

# ============ FUNÇÕES BÁSICAS ============
def calcular_nps(df):
    """Retorna (nps, %prom, %neut, %det, total)"""
    if df.empty or "NPS_Recomendacao" not in df.columns:
        return 0.0, 0.0, 0.0, 0.0, 0
    total = len(df)
    promotores = (pd.to_numeric(df["NPS_Recomendacao"], errors="coerce").fillna(0).astype(int) >= 9).sum()
    detratores = (pd.to_numeric(df["NPS_Recomendacao"], errors="coerce").fillna(0).astype(int) <= 6).sum()
    perc_prom = (promotores / total) * 100 if total else 0
    perc_det = (detratores / total) * 100 if total else 0
    perc_neut = max(0.0, 100 - perc_prom - perc_det)
    nps = perc_prom - perc_det
    return nps, perc_prom, perc_neut, perc_det, total

@st.cache_data
def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def formatar_data(d):
    digits = "".join(c for c in d if c.isdigit())
    if len(digits) == 8:
        return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"
    return d

# ============ GOOGLE SHEETS HELPER ============
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

def save_response_to_sheet(row_dict):
    _, ws = get_sheet_handles()
    if ws is None:
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

def load_responses_from_sheet() -> pd.DataFrame:
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

# ============ ESTADOS ============
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

# ============ MODO ADMIN ============
query = st.query_params
admin_mode = (ADMIN_KEY in query and query[ADMIN_KEY] == ADMIN_PASSWORD)

# =========================================================
# DASHBOARD ADMINISTRATIVO
# =========================================================
if admin_mode:
    st.markdown("## 🔐 Dashboard Administrativo")
    df = load_responses_from_sheet()

    if df.empty:
        st.warning("Ainda não há respostas coletadas.")
    else:
        for col in ["Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente","Nota_Pedido_Embalagem","NPS_Recomendacao"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        nps_geral, prom_g, neut_g, det_g, total = calcular_nps(df)
        df_salao = df[df["Segmento"] == "Restaurante (Salão)"]
        df_delivery = df[df["Segmento"] == "Delivery (Entrega)"]
        nps_salao, *_ = calcular_nps(df_salao)
        nps_delivery, *_ = calcular_nps(df_delivery)

        colA, colB, colC, colD = st.columns(4)
        colA.metric("Total de Respostas", f"{total}")
        colB.metric("NPS Geral", f"{nps_geral:.1f}")
        colC.metric("Total Salão", f"{len(df_salao)}")
        colD.metric("Total Delivery", f"{len(df_delivery)}")

        st.markdown("---")
        st.markdown("### 📈 NPS por experiência")
        nps_df = pd.DataFrame({
            "Categoria": ["Geral", "Salão", "Delivery"],
            "NPS": [round(nps_geral, 1), round(nps_salao, 1), round(nps_delivery, 1)]
        })
        bar = (
            alt.Chart(nps_df)
            .mark_bar()
            .encode(
                x=alt.X("Categoria:N", title=""),
                y=alt.Y("NPS:Q", scale=alt.Scale(domain=[-100, 100])),
                tooltip=["Categoria:N","NPS:Q"]
            )
            .properties(height=320)
        )
        labels = (
            alt.Chart(nps_df)
            .mark_text(dy=-10)
            .encode(x="Categoria:N", y="NPS:Q", text=alt.Text("NPS:Q"))
        )
        st.altair_chart(bar + labels, use_container_width=True)

        st.markdown("### 🥧 Distribuição de experiências")
        dist_df = pd.DataFrame({
            "Experiência": ["Salão", "Delivery"],
            "Quantidade": [len(df_salao), len(df_delivery)]
        })
        if dist_df["Quantidade"].sum() == 0:
            dist_df.loc[0, "Quantidade"] = 1

        pie = (
            alt.Chart(dist_df)
            .mark_arc(innerRadius=60)
            .encode(
                theta="Quantidade:Q",
                color=alt.Color("Experiência:N", legend=alt.Legend(title="Experiência")),
                tooltip=["Experiência:N", "Quantidade:Q"]
            )
            .properties(height=320)
        )
        st.altair_chart(pie, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🧾 Respostas coletadas")
        csv = to_csv_bytes(df.sort_values(by="Data", ascending=False))
        st.download_button("📥 Baixar Respostas (CSV)", csv, "respostas_pesquisa.csv", "text/csv")
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)

# =========================================================
# MODO PÚBLICO (FORMULÁRIO + MENSAGENS)
# =========================================================
else:
    if not st.session_state.submitted:
        st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós!</p>", unsafe_allow_html=True)
        st.markdown("---")

        segmento = st.radio("**Sua compra na Pureto foi?**", ["Restaurante (Salão)", "Delivery (Entrega)"], horizontal=True)
        st.markdown("---")

        if segmento == "Restaurante (Salão)":
            opcoes_conheceu = [
                "Selecione uma opção","Já era cliente do delivery","Instagram","Facebook","Google",
                "Indicação de amigo/familiar","Passando em frente ao restaurante","Outro:"
            ]
        else:
            opcoes_conheceu = [
                "Selecione uma opção","Já era cliente do salão","Instagram","Facebook","Google",
                "Indicação de amigo/familiar","Passando em frente ao restaurante","Outro:"
            ]

        como_conheceu = st.selectbox("Como nos conheceu?", opcoes_conheceu)
        como_outro = ""
        if como_conheceu == "Outro:":
            como_outro = st.text_input("Como nos conheceu? (Especifique):")

        with st.form("pesquisa_form"):
            st.subheader("Sobre você")
            col1, col2, col3 = st.columns(3)
            nome = col1.text_input("Seu nome completo:")
            whatsapp = col2.text_input("Seu WhatsApp:")
            aniversario_raw = col3.text_input("Data de aniversário (DD/MM/AAAA):", placeholder="Ex: 14101972")
            aniversario = formatar_data(aniversario_raw)

            st.markdown("---")
            opcoes = list(range(0, 11))
            if segmento == "Restaurante (Salão)":
                nota_atend = st.radio("1️⃣ Atendimento:", opcoes, horizontal=True)
                nota_sabor = st.radio("2️⃣ Sabor:", opcoes, horizontal=True)
                nota_ambiente = st.radio("3️⃣ Ambiente:", opcoes, horizontal=True)
                nota_embalagem = ""
                nps = st.radio("4️⃣ Recomendação:", opcoes, horizontal=True)
            else:
                nota_atend = st.radio("1️⃣ Atendimento:", opcoes, horizontal=True)
                nota_embalagem = st.radio("2️⃣ Logística:", opcoes, horizontal=True)
                nota_sabor = st.radio("3️⃣ Sabor:", opcoes, horizontal=True)
                nota_ambiente = st.radio("4️⃣ Cuidado com os itens:", opcoes, horizontal=True)
                nps = st.radio("5️⃣ Recomendação:", opcoes, horizontal=True)

            comentario = st.text_area("💬 Comentário (opcional):")
            submit = st.form_submit_button("Enviar Respostas ✅")

        if submit:
            if not nome or not whatsapp:
                st.error("⚠️ Preencha Nome e WhatsApp.")
            else:
                nova_dict = {
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Nome": nome,
                    "Whatsapp": whatsapp,
                    "Aniversario": aniversario,
                    "Como_Conheceu": como_outro if como_conheceu == "Outro:" else como_conheceu,
                    "Segmento": segmento,
                    "Nota_Atendimento": nota_atend,
                    "Nota_Qualidade_Sabor": nota_sabor,
                    "Nota_Entrega_Ambiente": nota_ambiente,
                    "Nota_Pedido_Embalagem": nota_embalagem,
                    "NPS_Recomendacao": nps,
                    "Comentario": comentario
                }
                save_response_to_sheet(nova_dict)
                st.session_state.submitted = True
                st.session_state.ultimo_nome = nome
                st.session_state.ultimo_nps = nps
                st.rerun()

    else:
        nome_sucesso = st.session_state.ultimo_nome
        nps_sucesso = float(st.session_state.ultimo_nps)

        st.success("✅ Pesquisa enviada com sucesso!")
        st.markdown(f"""
        <div style='background-color:#e8f5e9; color:#1b5e20; padding:20px; border-radius:10px; margin-top:20px;'>
        <h3>🎉 {nome_sucesso}, muito obrigado pelas suas respostas sinceras!</h3>
        <p>Seu feedback é essencial para aperfeiçoarmos cada detalhe do <b>Pureto Sushi</b>.</p>
        <p>Como forma de agradecimento, você ganhou um <b>cupom especial de 10% de desconto</b> na sua próxima compra.</p>
        <p style='font-size:1.2em;'><b>Use o código:</b> <span style='color:#007bff;'>PESQUISA</span></p>
        </div>
        """, unsafe_allow_html=True)

        if float(nps_sucesso) >= 9:
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
            </div>
            """, unsafe_allow_html=True)

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

        st.markdown("---")
        st.info("Obrigado por contribuir!")
