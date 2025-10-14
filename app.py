# =========================================================
# PesquisaPureto_v1.2
# Sistema de Pesquisa de Satisfação do Pureto Sushi
# =========================================================

import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------------------------------------------------------
# CONFIGURAÇÕES GERAIS
# ---------------------------------------------------------
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")

GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"
CSV_PATH = "data/pesquisa_respostas.csv"
ADMIN_PASSWORD = "pureto2025"

# ---------------------------------------------------------
# FUNÇÃO DE CÁLCULO DO NPS
# ---------------------------------------------------------
def calcular_nps(df):
    if df.empty:
        return 0, 0, 0, 0, 0
    total = len(df)
    promotores = df[df['NPS_Recomendacao'] >= 9].count().NPS_Recomendacao
    detratores = df[df['NPS_Recomendacao'] <= 6].count().NPS_Recomendacao
    perc_prom = (promotores / total) * 100
    perc_det = (detratores / total) * 100
    nps_score = perc_prom - perc_det
    return nps_score, perc_prom, 100 - perc_prom - perc_det, perc_det, total


# ---------------------------------------------------------
# CARREGAR OU CRIAR BASE CSV
# ---------------------------------------------------------
if not os.path.exists("data"):
    os.makedirs("data")

if os.path.exists(CSV_PATH):
    df_base = pd.read_csv(CSV_PATH)
else:
    df_base = pd.DataFrame(columns=[
        'Data', 'Nome', 'Whatsapp', 'Aniversario', 'Como_Conheceu', 'Segmento',
        'Nota_Atendimento', 'Nota_Qualidade_Sabor', 'Nota_Entrega_Ambiente',
        'NPS_Recomendacao', 'Comentario'
    ])


# ---------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------
st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 1 minuto.</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------
# FORMULÁRIO PRINCIPAL
# ---------------------------------------------------------
with st.form(key="pesquisa_form"):
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("**Seu Nome Completo:**")
    whatsapp = col2.text_input("**Seu WhatsApp:**")
    aniversario = col3.date_input("**Data de Aniversário:**", value=datetime.today())

    segmento = st.radio(
        "**Onde foi sua experiência?**",
        ['Restaurante (Salão)', 'Delivery (Entrega)'],
        horizontal=True
    )

    st.markdown("---")

    # --- COMO CONHECEU ---
    if segmento == 'Restaurante (Salão)':
        opcoes_conheceu = ['Instagram', 'Facebook', 'Google', 'Indicação', 'Passando em frente', 'Outro:']
    else:
        opcoes_conheceu = ['Instagram', 'Facebook', 'Google', 'Indicação', 'Cliente do Salão', 'Outro:']

    como_conheceu = st.selectbox("**Como você nos conheceu?**", opcoes_conheceu)
    como_outro = ""
    if como_conheceu == "Outro:":
        como_outro = st.text_input("Por favor, especifique como nos conheceu:")

    st.markdown("---")

    # --- PERGUNTAS POR SEGMENTO ---
    opcoes = list(range(0, 11))

    if segmento == "Restaurante (Salão)":
        st.subheader("🍽️ Avaliação no Salão")
        nota_atendimento = st.radio("1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):", opcoes, horizontal=True)
        nota_qualidade = st.radio("2️⃣ Qualidade e sabor dos pratos:", opcoes, horizontal=True)
        nota_entrega_ambiente = st.radio("3️⃣ Ambiente e limpeza:", opcoes, horizontal=True)
    else:
        st.subheader("🛵 Avaliação do Delivery")
        nota_atendimento = st.radio("1️⃣ Atendimento e facilidade do pedido:", opcoes, horizontal=True)
        nota_qualidade = st.radio("2️⃣ Qualidade e sabor após entrega:", opcoes, horizontal=True)
        nota_entrega_ambiente = st.radio("3️⃣ Tempo e integridade da entrega:", opcoes, horizontal=True)

    nps_recomendacao = st.radio("⭐ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?", opcoes, horizontal=True)
    comentario = st.text_area("💬 Comentários, sugestões, elogios ou reclamações (opcional):", max_chars=500)

    enviar = st.form_submit_button("Enviar Respostas ✅")

# ---------------------------------------------------------
# PROCESSAR ENVIO
# ---------------------------------------------------------
if enviar:
    if not nome or not whatsapp:
        st.error("⚠️ Por favor, preencha Nome e WhatsApp.")
    else:
        aniversario_str = aniversario.strftime("%d/%m/%Y")
        como_final = como_outro if como_conheceu == "Outro:" else como_conheceu

        nova = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Nome": nome,
            "Whatsapp": whatsapp,
            "Aniversario": aniversario_str,
            "Como_Conheceu": como_final,
            "Segmento": segmento,
            "Nota_Atendimento": nota_atendimento,
            "Nota_Qualidade_Sabor": nota_qualidade,
            "Nota_Entrega_Ambiente": nota_entrega_ambiente,
            "NPS_Recomendacao": nps_recomendacao,
            "Comentario": comentario
        }])

        df_base = pd.concat([df_base, nova], ignore_index=True)
        df_base.to_csv(CSV_PATH, index=False)

        # ✅ Mensagem padrão
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

        # ⭐ Mensagem condicional
        if nps_recomendacao > 8:
            st.markdown(
                f"""
                <div style='background-color:#fff3cd; color:#856404; padding:20px; border-radius:10px; margin-top:25px;'>
                    <h4>🌟 {nome}, já que você nos avaliou tão bem, gostaríamos de pedir uma última ajuda!</h4>
                    <p>Seria incrível se você pudesse deixar uma avaliação rápida no Google sobre sua experiência. Isso nos ajuda demais!</p>
                    <a href='{GOOGLE_REVIEW_LINK}' target='_blank'
                    style='background-color:#f0ad4e; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;'>
                        💬 Avaliar no Google
                    </a>
                </div>
                """, unsafe_allow_html=True
            )
            st.balloons()

        st.info("✅ Suas respostas foram registradas com sucesso. Obrigado por contribuir!")

# ---------------------------------------------------------
# ÁREA ADMINISTRATIVA
# ---------------------------------------------------------
st.markdown("---")
st.markdown("### 🔐 Acesso Administrativo")
senha = st.text_input("Digite a senha de administrador:", type="password")

if senha == ADMIN_PASSWORD:
    st.success("Acesso liberado ✅")
    if not df_base.empty:
        nps, prom, neut, det, total = calcular_nps(df_base)
        st.metric("NPS Geral", f"{nps:.1f}")
        st.metric("Total de respostas", total)

        st.download_button(
            label="⬇️ Baixar Relatório Completo (CSV)",
            data=df_base.to_csv(index=False).encode('utf-8'),
            file_name='relatorio_pesquisa_pureto.csv',
            mime='text/csv'
        )
        st.dataframe(df_base, use_container_width=True)
    else:
        st.warning("Ainda não há respostas registradas.")
elif senha != "":
    st.error("❌ Senha incorreta.")



NOVO


# =========================================================
# PesquisaPureto_v1.3 - Cliente
# Sistema de Pesquisa de Satisfação do Pureto Sushi
# =========================================================

import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------------------------------------------------------
# CONFIGURAÇÕES GERAIS
# ---------------------------------------------------------
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")

GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"
CSV_PATH = "data/pesquisa_respostas.csv"

# ---------------------------------------------------------
# CARREGAR OU CRIAR BASE CSV
# ---------------------------------------------------------
if not os.path.exists("data"):
    os.makedirs("data")

if os.path.exists(CSV_PATH):
    df_base = pd.read_csv(CSV_PATH)
else:
    df_base = pd.DataFrame(columns=[
        'Data', 'Nome', 'Whatsapp', 'Aniversario', 'Como_Conheceu', 'Segmento',
        'Nota_Atendimento', 'Nota_Qualidade_Sabor', 'Nota_Entrega_Ambiente',
        'NPS_Recomendacao', 'Comentario'
    ])

# ---------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------
st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 1 minuto.</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------
# FORMULÁRIO PRINCIPAL
# ---------------------------------------------------------
with st.form(key="pesquisa_form"):
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("**Seu Nome Completo:**")
    whatsapp = col2.text_input("**Seu WhatsApp:**")
    aniversario = col3.date_input("**Data de Aniversário:**", value=datetime.today())

    segmento = st.radio(
        "**Onde foi sua experiência?**",
        ['Restaurante (Salão)', 'Delivery (Entrega)'],
        horizontal=True
    )

    st.markdown("---")

    # --- COMO CONHECEU ---
    if segmento == 'Restaurante (Salão)':
        opcoes_conheceu = ['Instagram', 'Facebook', 'Google', 'Indicação', 'Passando em frente', 'Outro:']
    else:
        opcoes_conheceu = ['Instagram', 'Facebook', 'Google', 'Indicação', 'Cliente do Salão', 'Outro:']

    como_conheceu = st.selectbox("**Como você nos conheceu?**", opcoes_conheceu)
    como_outro = ""
    if como_conheceu == "Outro:":
        como_outro = st.text_input("Por favor, especifique como nos conheceu:")

    st.markdown("---")

    # --- PERGUNTAS POR SEGMENTO ---
    opcoes = list(range(0, 11))

    if segmento == "Restaurante (Salão)":
        st.subheader("🍽️ Avaliação no Salão")
        nota_atendimento = st.radio("1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):", opcoes, horizontal=True)
        nota_qualidade = st.radio("2️⃣ Qualidade e sabor dos pratos:", opcoes, horizontal=True)
        nota_entrega_ambiente = st.radio("3️⃣ Ambiente e limpeza:", opcoes, horizontal=True)
    else:
        st.subheader("🛵 Avaliação do Delivery")
        nota_atendimento = st.radio("1️⃣ Atendimento e facilidade do pedido:", opcoes, horizontal=True)
        nota_qualidade = st.radio("2️⃣ Qualidade e sabor após entrega:", opcoes, horizontal=True)
        nota_entrega_ambiente = st.radio("3️⃣ Tempo e integridade da entrega:", opcoes, horizontal=True)

    nps_recomendacao = st.radio("4️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?", opcoes, horizontal=True)
    comentario = st.text_area("💬 Comentários, sugestões, elogios ou reclamações (opcional):", max_chars=500)

    enviar = st.form_submit_button("Enviar Respostas ✅")

# ---------------------------------------------------------
# PROCESSAR ENVIO
# ---------------------------------------------------------
if enviar:
    if not nome or not whatsapp:
        st.error("⚠️ Por favor, preencha Nome e WhatsApp.")
    else:
        aniversario_str = aniversario.strftime("%d/%m/%Y")
        como_final = como_outro if como_conheceu == "Outro:" else como_conheceu

        nova = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Nome": nome,
            "Whatsapp": whatsapp,
            "Aniversario": aniversario_str,
            "Como_Conheceu": como_final,
            "Segmento": segmento,
            "Nota_Atendimento": nota_atendimento,
            "Nota_Qualidade_Sabor": nota_qualidade,
            "Nota_Entrega_Ambiente": nota_entrega_ambiente,
            "NPS_Recomendacao": nps_recomendacao,
            "Comentario": comentario
        }])

        df_base = pd.concat([df_base, nova], ignore_index=True)
        df_base.to_csv(CSV_PATH, index=False)

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

        if nps_recomendacao > 8:
            st.markdown(
                f"""
                <div style='background-color:#fff3cd; color:#856404; padding:20px; border-radius:10px; margin-top:25px;'>
                    <h4>🌟 {nome}, já que você nos avaliou tão bem, gostaríamos de pedir uma última ajuda!</h4>
                    <p>Seria incrível se você pudesse deixar uma avaliação rápida no Google sobre sua experiência. Isso nos ajuda demais!</p>
                    <a href='{GOOGLE_REVIEW_LINK}' target='_blank'
                    style='background-color:#f0ad4e; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;'>
                        💬 Avaliar no Google
                    </a>
                </div>
                """, unsafe_allow_html=True
            )
            st.balloons()

        st.info("✅ Suas respostas foram registradas com sucesso. Obrigado por contribuir!")



Sdmin
# =========================================================
# PesquisaPureto_v1.3 - Admin
# Área Administrativa do Pureto Sushi
# =========================================================

import streamlit as st
import pandas as pd
from datetime import datetime

CSV_PATH = "data/pesquisa_respostas.csv"
ADMIN_PASSWORD = "pureto2025"

st.set_page_config(page_title="Admin - Pureto Sushi", layout="wide")
st.title("🔐 Área Administrativa")

senha = st.text_input("Digite a senha de administrador:", type="password")

if senha == ADMIN_PASSWORD:
    st.success("Acesso liberado ✅")
    if not pd.read_csv(CSV_PATH).empty:
        df_base = pd.read_csv(CSV_PATH)

        def calcular_nps(df):
            total = len(df)
            promotores = df[df['NPS_Recomendacao'] >= 9].count().NPS_Recomendacao
            detratores = df[df['NPS_Recomendacao'] <= 6].count().NPS_Recomendacao
            perc_prom = (promotores / total) * 100
            perc_det = (detratores / total) * 100
            nps_score = perc_prom - perc_det
            return nps_score, perc_prom, 100 - perc_prom - perc_det, perc_det, total

        nps, prom, neut, det, total = calcular_nps(df_base)
        st.metric("NPS Geral", f"{nps:.1f}")
        st.metric("Total de respostas", total)

        st.download_button(
            label="⬇️ Baixar Relatório Completo (CSV)",
            data=df_base.to_csv(index=False).encode('utf-8'),
            file_name='relatorio_pesquisa_pureto.csv',
            mime='text/csv'
        )
        st.dataframe(df_base, use_container


