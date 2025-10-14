import streamlit as st
import pandas as pd
from datetime import datetime, date

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(page_title="Pesquisa de Satisfação — Pureto", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"

# ============================================================
# INICIALIZAÇÃO DE ESTADOS (ARMAZENAMENTO EM MEMÓRIA)
# ============================================================
if "respostas" not in st.session_state:
    st.session_state.respostas = pd.DataFrame(columns=[
        "Data", "Nome", "Whatsapp", "Aniversario", "Como_Conheceu",
        "Segmento", "Nota1", "Nota2", "Nota3", "Nota4", "Nota5", "NPS", "Comentario"
    ])

# ============================================================
# FUNÇÃO DE CÁLCULO NPS
# ============================================================
def calcular_nps(df):
    if df.empty:
        return 0, 0
    total = len(df)
    nps_scores = pd.to_numeric(df["NPS"])
    promotores = (nps_scores >= 9).sum()
    detratores = (nps_scores <= 6).sum()
    nps_score = ((promotores - detratores) / total) * 100
    return nps_score, total

# ============================================================
# ROTEAMENTO: ADMIN vs CLIENTE
# ============================================================
query_params = st.query_params

if "admin" in query_params and query_params["admin"] == "1":
    st.title("🔒 Painel Administrativo de Respostas")
    st.markdown("As respostas abaixo são coletadas na memória do aplicativo e serão perdidas se o app reiniciar.")
    st.warning("**IMPORTANTE:** Baixe o arquivo CSV regularmente para salvar as respostas permanentemente.")
    
    df = st.session_state.respostas
    
    if not df.empty:
        nps_geral, total_respostas = calcular_nps(df)
        
        col1, col2 = st.columns(2)
        col1.metric("NPS Geral", f"{nps_geral:.1f}")
        col2.metric("Total de Respostas", total_respostas)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar Respostas (CSV)",
            data=csv,
            file_name=f"respostas_pureto_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
            mime="text/csv",
        )
        
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
        
    else:
        st.info("Nenhuma resposta foi coletada ainda.")

else:
    st.title("Pesquisa de Satisfação")
    st.markdown("Sua opinião é muito importante para nós! Leva menos de 1 minuto.")

    segmento = st.radio(
        "Primeiro, conte pra gente: onde foi sua experiência?",
        ["Restaurante (Salão)", "Delivery (Entrega)"],
        horizontal=True, key="segmento_selecionado"
    )

    como_conheceu = st.selectbox(
        "Como você conheceu o Pureto?",
        ["Instagram", "Facebook", "Google", "Indicação", "Já era cliente do Delivery", "Já era cliente do Restaurante", "Outro"],
        key="como_conheceu_select"
    )
    
    como_conheceu_outro = ""
    if como_conheceu == "Outro":
        como_conheceu_outro = st.text_input(
            "Por favor, especifique como nos conheceu:",
            placeholder="Ex: Vi a fachada, Anúncio no rádio, etc.",
            key="como_conheceu_outro_text"
        )
    
    st.markdown("---")

    with st.form("formulario_cliente"):
        st.subheader("Conte-nos um pouco sobre você")
        col1, col2, col3 = st.columns([2, 2, 1])
        nome = col1.text_input("Seu Nome Completo:")
        whatsapp = col2.text_input("Seu WhatsApp (com DDD):")
        
        today = date.today()
        min_date = today.replace(year=today.year - 100)
        aniversario = col3.date_input(
            "Data de Aniversário:", value=None, min_value=min_date, max_value=today, format="DD/MM/YYYY"
        )
        
        st.markdown("---")

        if segmento == "Restaurante (Salão)":
            st.subheader("🍽️ Avaliação no Salão")
            nota1 = st.radio("1️⃣ Atendimento da equipe:", list(range(11)), horizontal=True, key="nota1_salao")
            nota2 = st.radio("2️⃣ Qualidade e sabor dos pratos:", list(range(11)), horizontal=True, key="nota2_salao")
            nota3 = st.radio("3️⃣ Limpeza e conforto do ambiente:", list(range(11)), horizontal=True, key="nota3_salao")
            nota4 = st.radio("4️⃣ O quanto você nos recomendaria?", list(range(11)), horizontal=True, key="nps_salao")
            nota5 = ""
            nps = nota4

        else:
            st.subheader("🛵 Avaliação do Delivery")
            nota1 = st.radio("1️⃣ Facilidade e atendimento no pedido:", list(range(11)), horizontal=True, key="nota1_delivery")
            nota2 = st.radio("2️⃣ Rapidez da entrega:", list(range(11)), horizontal=True, key="nota2_delivery")
            nota3 = st.radio("3️⃣ Qualidade e sabor dos pratos:", list(range(11)), horizontal=True, key="nota3_delivery")
            nota4 = st.radio("4️⃣ Condição da embalagem ao chegar:", list(range(11)), horizontal=True, key="nota4_delivery")
            nota5 = st.radio("5️⃣ O quanto você nos recomendaria?", list(range(11)), horizontal=True, key="nps_delivery")
            nps = nota5

        st.markdown("---")
        comentario = st.text_area("Comentários, sugestões ou elogios (opcional):", max_chars=500)
        
        submit = st.form_submit_button("Enviar Respostas")

    if submit:
        if not nome or not whatsapp or not aniversario:
            st.error("Por favor, preencha seu Nome, WhatsApp e Data de Aniversário.")
        else:
            como_conheceu_final = como_conheceu
            if como_conheceu == "Outro" and como_conheceu_outro:
                como_conheceu_final = f"Outro: {como_conheceu_outro}"

            aniversario_str = aniversario.strftime("%d/%m/%Y")
            
            nova_resposta = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Nome": nome, "Whatsapp": whatsapp,
                "Aniversario": aniversario_str, "Como_Conheceu": como_conheceu_final, "Segmento": segmento,
                "Nota1": nota1, "Nota2": nota2, "Nota3": nota3, "Nota4": nota4, "Nota5": str(nota5),
                "NPS": nps, "Comentario": comentario
            }])
            
            st.session_state.respostas = pd.concat([st.session_state.respostas, nova_resposta], ignore_index=True)

            st.success(f"{nome}, sua avaliação foi registrada com sucesso!")
            st.markdown("""
            <div style='background-color:#e8f5e9;padding:20px;border-radius:10px;text-align:center;'>
            <h4>Seu feedback é essencial para melhorarmos sempre! 🍣</h4>
            <p>Como agradecimento, use o cupom <b>PESQUISA10</b> e ganhe <b>10% de desconto</b>.</p>
            </div>
            """, unsafe_allow_html=True)
            if int(nps) >= 9:
                st.balloons()
                st.markdown(f"""
                <div style='background-color:#fff3cd;padding:20px;border-radius:10px;margin-top:20px;text-align:center;'>
                <h4>🌟 {nome}, sua opinião positiva vale ouro!</h4>
                <p>Que tal compartilhá-la no Google? Isso nos ajuda imensamente a crescer.</p>
                <a href='{GOOGLE_REVIEW_LINK}' target='_blank' style='display:inline-block; background:#f0ad4e;color:white;padding:12px 25px;border-radius:5px;text-decoration:none;font-weight:bold;'>Deixar Avaliação no Google</a>
                </div>
                """, unsafe_allow_html=True)

st.markdown("""
<hr style="margin-top: 50px;">
<div style='text-align:center; color:gray; font-size: 0.9em;'>
    <i>"Somos mais do que vencedores." — Romanos 8:37</i>
    <br>
    Desenvolvido por <b>Arsanjo</b>
</div>
""", unsafe_allow_html=True)
