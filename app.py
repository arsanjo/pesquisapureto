import streamlit as st
import pandas as pd
from datetime import datetime

# =========================================================
# CONFIGURAÇÃO GERAL
# =========================================================
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review" 

# =========================================================
# FUNÇÃO: CÁLCULO DO NPS
# =========================================================
def calcular_nps(df):
    if df.empty:
        return 0, 0, 0, 0, 0
    total = len(df)
    if 'NPS_Recomendacao' not in df.columns:
        return 0, 0, 0, 0, 0
        
    promotores = df[df['NPS_Recomendacao'] >= 9].shape[0]
    detratores = df[df['NPS_Recomendacao'] <= 6].shape[0]
    perc_prom = (promotores / total) * 100
    perc_det = (detratores / total) * 100
    perc_neut = 100 - perc_prom - perc_det
    nps_score = perc_prom - perc_det
    return nps_score, perc_prom, perc_neut, perc_det, total

# =========================================================
# ESTADOS INICIAIS
# =========================================================
if 'respostas' not in st.session_state:
    st.session_state.respostas = pd.DataFrame(columns=[
        'Data', 'Nome', 'Whatsapp', 'Aniversario', 'Como_Conheceu', 'Segmento',
        'Nota_Atendimento', 'Nota_Qualidade_Sabor', 'Nota_Entrega_Ambiente',
        'Nota_Pedido_Embalagem', 'NPS_Recomendacao', 'Comentario'
    ])

# =========================================================
# INTERFACE DO FORMULÁRIO
# =========================================================
st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40 segundos.</p>", unsafe_allow_html=True) 
st.markdown("---")

with st.form("pesquisa_form"):

    # 1️⃣ SEGMENTO
    segmento = st.radio(
        "**Sua compra na Pureto foi?**", 
        options=["Restaurante (Salão)", "Delivery (Entrega)"],
        horizontal=True,
        key='seg_radio'
    )
    st.markdown("---")

    # 2️⃣ DADOS PESSOAIS
    st.subheader("Sobre você")
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("**Seu nome completo:**")
    whatsapp = col2.text_input("**Seu WhatsApp:**")
    aniversario = col3.text_input("**Data de aniversário (DD/MM/AAAA):**", placeholder="Ex: 25/12/1990")

    # 3️⃣ COMO CONHECEU
    st.markdown("---")
    if segmento == "Restaurante (Salão)":
        opcoes_conheceu = ["Selecione uma opção", "Já era cliente do delivery", "Instagram", "Facebook", "Google",
                           "Indicação de amigo/familiar", "Passando em frente ao restaurante",
                           "Placa na entrada de Schroeder (ponte)", "Outro:"]
    else:
        opcoes_conheceu = ["Selecione uma opção", "Já era cliente do salão", "Instagram", "Facebook", "Google",
                           "Indicação de amigo/familiar", "Passando em frente ao restaurante",
                           "Placa na entrada de Schroeder (ponte)", "Outro:"]

    como_conheceu = st.selectbox("**Como nos conheceu?**", opcoes_conheceu)

    # Campo "Outro" só aparece se selecionado
    if como_conheceu == "Outro:":
        como_conheceu_outro = st.text_input("Como nos conheceu? (Especifique):")
    else:
        como_conheceu_outro = ""

    st.markdown("---")

    # =========================================================
    # 4️⃣ PERGUNTAS AVALIATIVAS
    # =========================================================
    opcoes_notas = list(range(0, 11))

    if segmento == "Restaurante (Salão)":
        st.subheader("🍽️ Avaliação no Salão")
        nota_atendimento = st.radio("1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):", opcoes_notas, horizontal=True)
        nota_qualidade_sabor = st.radio("2️⃣ Qualidade e sabor dos pratos:", opcoes_notas, horizontal=True)
        nota_ambiente = st.radio("3️⃣ Ambiente e limpeza:", opcoes_notas, horizontal=True)
        nota_embalagem = None
        nps = st.radio("4️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?", opcoes_notas, horizontal=True)
    else:
        st.subheader("🛵 Avaliação do Delivery")
        nota_atendimento = st.radio("1️⃣ Atendimento e facilidade do pedido:", opcoes_notas, horizontal=True)
        nota_embalagem = st.radio("2️⃣ Logística (tempo e embalagem):", opcoes_notas, horizontal=True)
        nota_qualidade_sabor = st.radio("3️⃣ Qualidade e sabor pós-entrega:", opcoes_notas, horizontal=True)
        nota_ambiente = st.radio("4️⃣ Apresentação e cuidado com os itens:", opcoes_notas, horizontal=True)
        nps = st.radio("5️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?", opcoes_notas, horizontal=True)

    st.markdown("---")

    comentario = st.text_area("💬 Comentários, sugestões, elogios ou reclamações (opcional):", max_chars=500)

    enviar = st.form_submit_button("Enviar Respostas ✅")

# =========================================================
# PROCESSAMENTO DE RESPOSTA
# =========================================================
if enviar:
    # Validação
    if not nome or not whatsapp or como_conheceu == "Selecione uma opção":
        st.error("⚠️ Por favor, preencha Nome, WhatsApp e Como nos conheceu.")
    else:
        # Conversão e salvamento
        aniversario_fmt = aniversario.strip()
        if aniversario_fmt:
            try:
                aniversario_dt = datetime.strptime(aniversario_fmt, "%d/%m/%Y")
                aniversario_fmt = aniversario_dt.strftime("%d/%m/%Y")
            except ValueError:
                st.warning("⚠️ Data inválida. Use o formato DD/MM/AAAA.")
                st.stop()

        como_final = como_conheceu_outro if como_conheceu == "Outro:" else como_conheceu

        nova = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Nome": nome,
            "Whatsapp": whatsapp,
            "Aniversario": aniversario_fmt,
            "Como_Conheceu": como_final,
            "Segmento": segmento,
            "Nota_Atendimento": nota_atendimento,
            "Nota_Qualidade_Sabor": nota_qualidade_sabor,
            "Nota_Entrega_Ambiente": nota_ambiente,
            "Nota_Pedido_Embalagem": nota_embalagem,
            "NPS_Recomendacao": nps,
            "Comentario": comentario
        }])

        st.session_state.respostas = pd.concat([st.session_state.respostas, nova], ignore_index=True)

        # ✅ Mensagens de agradecimento (mantidas)
        st.success("✅ Pesquisa enviada com sucesso!")
        st.markdown(
            f"""
            <div style='background-color:#e8f5e9; color:#1b5e20; padding:20px; border-radius:10px; margin-top:20px;'>
                <h3>🎉 {nome}, muito obrigado pelas suas respostas sinceras!</h3>
                <p>Seu feedback é essencial para aperfeiçoarmos cada detalhe do <b>Pureto Sushi</b>.</p>
                <p>Para agradecer, você ganhou um <b>cupom especial de 10% de desconto</b> na sua próxima compra.</p>
                <p style='font-size:1.2em;'><b>Use o código:</b> <span style='color:#007bff;'>PESQUISA</span></p>
            </div>
            """, unsafe_allow_html=True
        )

        if nps > 8:
            st.balloons()
            st.markdown(
                f"""
                <div style='background-color:#fff3cd; color:#856404; padding:20px; border-radius:10px; margin-top:25px;'>
                    <h4 style='font-weight:bold; color:#856404;'>Google <span style='font-size:1.5em;'>⭐⭐⭐⭐⭐</span></h4>
                    <p>{nome}, e que tal compartilhar essa sua incrível opinião lá no Google com um comentário positivo? Isso nos ajuda muito! 🙏</p>
                    <p style='font-weight:bold;'>Como gratidão por essa parte, sua próxima entrega é grátis.</p>
                    <a href='{GOOGLE_REVIEW_LINK}' target='_blank'
                    style='background-color:#f0ad4e; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;'>
                        💬 Avaliar no Google
                    </a>
                </div>
                """, unsafe_allow_html=True
            )
