import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt  # ✅ usamos Altair para gráficos, já incluído no Streamlit

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"
INSTAGRAM_LINK = "https://www.instagram.com/puretosushi"
ADMIN_KEY = "admin"
ADMIN_PASSWORD = "pureto2025"

# =========================================================
# FUNÇÕES
# =========================================================
def calcular_nps(df):
    """Retorna (nps, %prom, %neut, %det, total)"""
    if df.empty or "NPS_Recomendacao" not in df.columns:
        return 0.0, 0.0, 0.0, 0.0, 0
    total = len(df)
    promotores = (df["NPS_Recomendacao"] >= 9).sum()
    detratores = (df["NPS_Recomendacao"] <= 6).sum()
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

# =========================================================
# ESTADOS
# =========================================================
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

# =========================================================
# CHECAGEM DE MODO ADMIN
# =========================================================
query = st.query_params
admin_mode = (ADMIN_KEY in query and query[ADMIN_KEY] == ADMIN_PASSWORD)

# =========================================================
# DASHBOARD ADMINISTRATIVO (exclusivo quando ?admin=pureto2025)
# =========================================================
if admin_mode:
    st.markdown("## 🔐 Dashboard Administrativo")

    df = st.session_state.respostas.copy()

    if df.empty:
        st.warning("Ainda não há respostas coletadas.")
    else:
        # Conversões seguras
        df["NPS_Recomendacao"] = pd.to_numeric(df["NPS_Recomendacao"], errors="coerce").fillna(0).astype(int)

        # Resumos
        nps_geral, prom_g, neut_g, det_g, total = calcular_nps(df)
        df_salao = df[df["Segmento"] == "Restaurante (Salão)"]
        df_delivery = df[df["Segmento"] == "Delivery (Entrega)"]
        nps_salao, *_ = calcular_nps(df_salao)
        nps_delivery, *_ = calcular_nps(df_delivery)

        with st.container():
            colA, colB, colC, colD = st.columns(4)
            colA.metric("Total de Respostas", f"{total}")
            colB.metric("NPS Geral", f"{nps_geral:.1f}")
            colC.metric("Total Salão", f"{len(df_salao)}")
            colD.metric("Total Delivery", f"{len(df_delivery)}")

        st.markdown("---")
        st.markdown("### 📈 NPS por experiência")

        # ---------- Gráfico de barras (Altair): NPS Geral x Salão x Delivery ----------
        nps_df = pd.DataFrame({
            "Categoria": ["Geral", "Salão", "Delivery"],
            "NPS": [round(nps_geral, 1), round(nps_salao, 1), round(nps_delivery, 1)]
        })
        bar = (
            alt.Chart(nps_df)
            .mark_bar()
            .encode(x=alt.X("Categoria:N", title=""), y=alt.Y("NPS:Q", scale=alt.Scale(domain=[-100, 100])))
            .properties(height=320)
        )
        labels = (
            alt.Chart(nps_df)
            .mark_text(dy=-10)
            .encode(x="Categoria:N", y="NPS:Q", text=alt.Text("NPS:Q"))
        )
        st.altair_chart(bar + labels, use_container_width=True)

        # ---------- Gráfico de pizza (Altair): proporção Salão vs Delivery ----------
        st.markdown("### 🥧 Distribuição de experiências")
        dist_df = pd.DataFrame({
            "Experiência": ["Salão", "Delivery"],
            "Quantidade": [len(df_salao), len(df_delivery)]
        })
        if dist_df["Quantidade"].sum() == 0:
            dist_df.loc[0, "Quantidade"] = 1  # evita erro com pizza vazia

        pie = (
            alt.Chart(dist_df)
            .mark_arc(innerRadius=60)  # donut
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
        csv = to_csv_bytes(df)
        st.download_button("📥 Baixar Respostas (CSV)", csv, "respostas_pesquisa.csv", "text/csv")
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)

# =========================================================
# MODO PÚBLICO (formulário e mensagens) — só quando NÃO é admin
# =========================================================
else:
    if not st.session_state.submitted:
        # Título
        st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40 segundos.</p>", unsafe_allow_html=True)
        st.markdown("---")

        segmento = st.radio("**Sua compra na Pureto foi?**", ["Restaurante (Salão)", "Delivery (Entrega)"], horizontal=True, key="segmento_selecionado")
        st.markdown("---")

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
            como_outro = st.text_input("Como nos conheceu? (Especifique):", value=st.session_state.como_outro_input_value, key="como_outro_input")
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
            aniversario = formatar_data(aniversario_raw)

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
            elif aniversario and (aniversario == aniversario_raw or len(aniversario_raw) != 8):
                st.error("⚠️ Data de aniversário inválida. Por favor, use 8 dígitos (DDMMAAAA).")
            else:
                como_conheceu_final = como_outro if como_conheceu == "Outro:" else como_conheceu
                nova = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Nome": nome,
                    "Whatsapp": whatsapp,
                    "Aniversario": aniversario,
                    "Como_Conheceu": como_conheceu_final,
                    "Segmento": segmento,
                    "Nota_Atendimento": nota_atend,
                    "Nota_Qualidade_Sabor": nota_sabor,
                    "Nota_Entrega_Ambiente": nota_ambiente,
                    "Nota_Pedido_Embalagem": nota_embalagem,
                    "NPS_Recomendacao": nps,
                    "Comentario": comentario
                }])
                st.session_state.respostas = pd.concat([st.session_state.respostas, nova], ignore_index=True)

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

        # CTA INSTAGRAM (sempre)
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
