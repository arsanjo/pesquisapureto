import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(page_title="Pesquisa de Satisfação — Pureto Sushi & Burger", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"

# ============================================================
# INICIALIZAÇÃO DE ESTADOS
# ============================================================
if "respostas" not in st.session_state:
    st.session_state.respostas = pd.DataFrame(columns=[
        "Data", "Nome", "Whatsapp", "Aniversario", "Como_Conheceu",
        "Segmento", "Nota1", "Nota2", "Nota3", "Nota4", "Nota5", "NPS", "Comentario"
    ])

if "ultimo_segmento" not in st.session_state:
    st.session_state.ultimo_segmento = None

# ============================================================
# FUNÇÃO DE CÁLCULO NPS
# ============================================================
def calcular_nps(df):
    if df.empty:
        return 0, 0, 0, 0, 0
    total = len(df)
    promotores = df[df["NPS"] >= 9].count().NPS
    detratores = df[df["NPS"] <= 6].count().NPS
    perc_prom = (promotores / total) * 100
    perc_det = (detratores / total) * 100
    perc_neut = 100 - perc_prom - perc_det
    nps_score = perc_prom - perc_det
    return nps_score, perc_prom, perc_neut, perc_det, total

# ============================================================
# INTERFACE PRINCIPAL (CLIENTE)
# ============================================================
st.title("Pesquisa de Satisfação")
st.markdown("Sua opinião é muito importante para nós! Leva menos de 1 minuto.")

with st.form("formulario"):
    col1, col2, col3 = st.columns([2, 2, 1])
    nome = col1.text_input("Seu Nome Completo:")
    whatsapp = col2.text_input("Seu WhatsApp:")
    aniversario = col3.date_input("Data de Aniversário:", value=datetime.today(),
                                  format="DD/MM/YYYY")

    segmento = st.radio("Onde foi sua experiência?", ["Restaurante (Salão)", "Delivery (Entrega)"], horizontal=True)
    como_conheceu = st.selectbox(
        "Como você conheceu o Pureto?",
        ["Instagram", "Facebook", "Google", "Indicação de amigo ou familiar",
         "Já era cliente do Delivery", "Já era cliente do Restaurante", "Outro"]
    )

    st.markdown("---")

    # ============================================================
    # PERGUNTAS DINÂMICAS (corrigido)
    # ============================================================
    if "ultimo_segmento" not in st.session_state or st.session_state.ultimo_segmento != segmento:
        for k in ["nota1", "nota2", "nota3", "nota4", "nota5"]:
            if k in st.session_state:
                del st.session_state[k]
        st.session_state.ultimo_segmento = segmento
        st.rerun()

    if segmento == "Restaurante (Salão)":
        st.subheader("🍽️ Avaliação no Salão")
        nota1 = st.radio("1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):", list(range(11)), key="nota1", horizontal=True)
        nota2 = st.radio("2️⃣ Qualidade e sabor dos pratos:", list(range(11)), key="nota2", horizontal=True)
        nota3 = st.radio("3️⃣ Limpeza e conforto do ambiente:", list(range(11)), key="nota3", horizontal=True)
        nota4 = st.radio("4️⃣ O quanto você nos recomendaria a um amigo ou familiar?", list(range(11)), key="nota4", horizontal=True)
        nota5 = None
        nps = nota4

    elif segmento == "Delivery (Entrega)":
        st.subheader("🚗 Avaliação do Delivery")
        nota1 = st.radio("1️⃣ Facilidade e atendimento no pedido:", list(range(11)), key="nota1", horizontal=True)
        nota2 = st.radio("2️⃣ Rapidez da entrega:", list(range(11)), key="nota2", horizontal=True)
        nota3 = st.radio("3️⃣ Qualidade e sabor dos pratos entregues:", list(range(11)), key="nota3", horizontal=True)
        nota4 = st.radio("4️⃣ Condição da embalagem ao chegar:", list(range(11)), key="nota4", horizontal=True)
        nota5 = st.radio("5️⃣ O quanto você nos recomendaria a um amigo ou familiar?", list(range(11)), key="nota5", horizontal=True)
        nps = nota5

    st.markdown("---")
    comentario = st.text_area("Comentários, sugestões, elogios ou reclamações (opcional):", max_chars=500)
    submit = st.form_submit_button("Enviar Respostas")

# ============================================================
# ENVIO E FEEDBACK
# ============================================================
if submit:
    if not nome:
        st.error("Por favor, preencha seu nome.")
    else:
        aniversario_str = aniversario.strftime("%d/%m/%Y")
        nova_resposta = pd.DataFrame({
            "Data": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Nome": [nome],
            "Whatsapp": [whatsapp],
            "Aniversario": [aniversario_str],
            "Como_Conheceu": [como_conheceu],
            "Segmento": [segmento],
            "Nota1": [nota1],
            "Nota2": [nota2],
            "Nota3": [nota3],
            "Nota4": [nota4],
            "Nota5": [nota5],
            "NPS": [nps],
            "Comentario": [comentario]
        })
        st.session_state.respostas = pd.concat([st.session_state.respostas, nova_resposta], ignore_index=True)

        # Mensagem geral
        st.success(f"{nome}, muito obrigado pelas suas respostas sinceras!")
        st.markdown("""
        <div style='background-color:#e8f5e9;padding:20px;border-radius:10px;'>
        <h4>Seu feedback é essencial para aperfeiçoarmos cada detalhe do Pureto Sushi 🍣</h4>
        <p>Como forma de agradecimento, você ganhou um cupom especial de <b>10% de desconto</b> na sua próxima compra.</p>
        <p><b>Use o código:</b> <span style='color:#1565c0;'>PESQUISA</span></p>
        </div>
        """, unsafe_allow_html=True)

        if nps >= 9:
            st.balloons()
            st.markdown(f"""
            <div style='background-color:#fff3cd;padding:20px;border-radius:10px;margin-top:10px;'>
            <h4>🌟 {nome}, já que você nos avaliou tão bem...</h4>
            <p>Seria incrível se você pudesse deixar uma <b>avaliação rápida no Google</b> sobre sua experiência.</p>
            <a href='{GOOGLE_REVIEW_LINK}' target='_blank' style='background:#f0ad4e;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;'>Deixar Avaliação no Google</a>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# PAINEL ADMINISTRATIVO (ACESSO SECRETO)
# ============================================================
query_params = st.query_params
if "admin" in query_params and query_params["admin"] == "1":
    st.title("🔒 Painel Administrativo")
    senha = st.text_input("Digite a senha de administrador:", type="password")
    if senha == os.getenv("ADMIN_PASSWORD", "pureto2025"):
        st.success("Acesso autorizado ✅")
        df = st.session_state.respostas
        if not df.empty:
            nps_geral, _, _, _, _ = calcular_nps(df)
            st.metric("NPS Geral", f"{nps_geral:.1f}")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar Respostas (CSV)", csv, "respostas_pesquisa.csv", "text/csv")
            st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
        else:
            st.info("Nenhuma resposta coletada ainda.")
    elif senha:
        st.error("Senha incorreta.")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("""
<hr>
<div style='text-align:center; color:gray;'>
Desenvolvido por <b>Arsanjo</b> — Romanos 8:37<br>
<i>"Somos mais do que vencedores."</i>
</div>
""", unsafe_allow_html=True)
