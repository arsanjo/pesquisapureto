import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"
ADMIN_KEY = "admin"
ADMIN_PASSWORD = "pureto2025"

# =========================================================
# FUNÇÕES
# =========================================================
def calcular_nps(df):
    if df.empty or "NPS_Recomendacao" not in df.columns:
        return 0, 0, 0, 0, 0
    total = len(df)
    promotores = (df["NPS_Recomendacao"] >= 9).sum()
    detratores = (df["NPS_Recomendacao"] <= 6).sum()
    perc_prom = (promotores / total) * 100
    perc_det = (detratores / total) * 100
    perc_neut = 100 - perc_prom - perc_det
    nps = perc_prom - perc_det
    return nps, perc_prom, perc_neut, perc_det, total

def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def formatar_data(d):
    """Adiciona / automaticamente e valida formato DD/MM/AAAA"""
    digits = "".join(c for c in d if c.isdigit())
    if len(digits) >= 8:
        return f"{digits[:2]}/{digits[2:4]}/{digits[4:8]}"
    elif len(digits) >= 4:
        return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"
    elif len(digits) >= 2:
        return f"{digits[:2]}/{digits[2:]}"
    return digits

# =========================================================
# ESTADOS
# =========================================================
if "respostas" not in st.session_state:
    st.session_state.respostas = pd.DataFrame(columns=[
        "Data","Nome","Whatsapp","Aniversario","Como_Conheceu","Segmento",
        "Nota_Atendimento","Nota_Qualidade_Sabor","Nota_Entrega_Ambiente",
        "Nota_Pedido_Embalagem","NPS_Recomendacao","Comentario"
    ])

# =========================================================
# TÍTULO
# =========================================================
st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40 segundos.</p>", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# FORMULÁRIO
# =========================================================
with st.form("pesquisa_form"):
    segmento = st.radio("**Sua compra na Pureto foi?**", ["Restaurante (Salão)", "Delivery (Entrega)"], horizontal=True)
    st.markdown("---")

    st.subheader("Sobre você")
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("Seu nome completo:")
    whatsapp = col2.text_input("Seu WhatsApp:")
    aniversario_raw = col3.text_input("Data de aniversário (DD/MM/AAAA):", placeholder="Ex: 14/10/2025")
    aniversario = formatar_data(aniversario_raw)

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

    st.markdown("---")
    opcoes = list(range(0, 11))

    if segmento == "Restaurante (Salão)":
        st.subheader("🍽️ Avaliação do Salão")
        nota_atend = st.radio("1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):", opcoes, horizontal=True)
        nota_sabor = st.radio("2️⃣ Qualidade e sabor dos pratos:", opcoes, horizontal=True)
        nota_ambiente = st.radio("3️⃣ Ambiente e limpeza:", opcoes, horizontal=True)
        nota_embalagem = None
        nps = st.radio("4️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria?", opcoes, horizontal=True)
    else:
        st.subheader("🛵 Avaliação do Delivery")
        nota_atend = st.radio("1️⃣ Atendimento e facilidade do pedido:", opcoes, horizontal=True)
        nota_embalagem = st.radio("2️⃣ Logística (tempo e embalagem):", opcoes, horizontal=True)
        nota_sabor = st.radio("3️⃣ Qualidade e sabor pós-entrega:", opcoes, horizontal=True)
        nota_ambiente = st.radio("4️⃣ Apresentação e cuidado com os itens:", opcoes, horizontal=True)
        nps = st.radio("5️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria?", opcoes, horizontal=True)

    comentario = st.text_area("💬 Comentários, sugestões, elogios ou reclamações (opcional):", max_chars=500)
    enviar = st.form_submit_button("Enviar Respostas ✅")

# =========================================================
# CAMPO “OUTRO” (fora do formulário → atualiza instantaneamente)
# =========================================================
if st.session_state.get("conheceu_select") == "Outro:":
    como_outro = st.text_input("Como nos conheceu? (Especifique):", key="como_outro_input")
else:
    como_outro = ""

# =========================================================
# PROCESSAMENTO
# =========================================================
if enviar:
    if not nome or not whatsapp or st.session_state.get("conheceu_select") == "Selecione uma opção":
        st.error("⚠️ Por favor, preencha Nome, WhatsApp e Como nos conheceu.")
    else:
        # valida data
        aniversario_fmt = ""
        try:
            if aniversario:
                datetime.strptime(aniversario, "%d/%m/%Y")
                aniversario_fmt = aniversario
        except ValueError:
            st.warning("⚠️ Data inválida. Use o formato DD/MM/AAAA.")
            st.stop()

        nova = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Nome": nome,
            "Whatsapp": whatsapp,
            "Aniversario": aniversario_fmt,
            "Como_Conheceu": como_outro if st.session_state.get("conheceu_select") == "Outro:" else st.session_state.get("conheceu_select"),
            "Segmento": segmento,
            "Nota_Atendimento": nota_atend,
            "Nota_Qualidade_Sabor": nota_sabor,
            "Nota_Entrega_Ambiente": nota_ambiente,
            "Nota_Pedido_Embalagem": nota_embalagem,
            "NPS_Recomendacao": nps,
            "Comentario": comentario
        }])
        st.session_state.respostas = pd.concat([st.session_state.respostas, nova], ignore_index=True)

        st.success("✅ Pesquisa enviada com sucesso!")
        st.markdown(f"""
        <div style='background-color:#e8f5e9; color:#1b5e20; padding:20px; border-radius:10px; margin-top:20px;'>
        <h3>🎉 {nome}, muito obrigado pelas suas respostas sinceras!</h3>
        <p>Seu feedback é essencial para aperfeiçoarmos cada detalhe do <b>Pureto Sushi</b>.</p>
        <p>Para agradecer, você ganhou um <b>cupom especial de 10% de desconto</b> na sua próxima compra.</p>
        <p style='font-size:1.2em;'><b>Use o código:</b> <span style='color:#007bff;'>PESQUISA</span></p>
        </div>
        """, unsafe_allow_html=True)

        if nps >= 9:
            st.balloons()
            st.markdown(f"""
            <div style='background-color:#fff3cd; color:#856404; padding:20px; border-radius:10px; margin-top:25px;'>
            <h4 style='font-weight:bold;'>Google ⭐⭐⭐⭐⭐</h4>
            <p>{nome}, e que tal compartilhar sua opinião lá no Google? Isso nos ajuda muito! 🙏</p>
            <p><b>Como gratidão, sua próxima entrega é grátis!</b></p>
            <a href='{GOOGLE_REVIEW_LINK}' target='_blank'
               style='background-color:#f0ad4e; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;'>
               💬 Avaliar no Google
            </a>
            </div>""", unsafe_allow_html=True)

# =========================================================
# ADMIN (via URL ?admin=pureto2025)
# =========================================================
query = st.query_params
if ADMIN_KEY in query and query[ADMIN_KEY] == ADMIN_PASSWORD:
    st.markdown("---")
    st.title("🔐 Dashboard Administrativo")
    df = st.session_state.respostas
    if len(df) > 0:
        nps, p, n, d, t = calcular_nps(df)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("NPS", f"{nps:.1f}")
        c2.metric("Promotores (%)", f"{p:.1f}")
        c3.metric("Neutros (%)", f"{n:.1f}")
        c4.metric("Detratores (%)", f"{d:.1f}")
        c5.metric("Total", t)
        st.download_button("⬇️ Baixar CSV", data=to_csv_bytes(df),
                           file_name="relatorio_pureto.csv", mime="text/csv")
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
    else:
        st.warning("Nenhuma resposta registrada ainda.")
