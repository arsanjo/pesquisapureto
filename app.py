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
    promotores = df[df['NPS_Recomendacao'] >= 9].shape[0]
    detratores = df[df['NPS_Recomendacao'] <= 6].shape[0]
    perc_prom = (promotores / total) * 100
    perc_det = (detratores / total) * 100
    perc_neut = 100 - perc_prom - perc_det
    nps_score = perc_prom - perc_det
    return nps_score, perc_prom, perc_neut, perc_det, total

# =========================================================
# ESTADOS INICIAIS (COLETA DE DADOS - ARMAZENAMENTO TEMPORÁRIO)
# NOTA: Esta versão armazena dados APENAS durante a sessão do Streamlit Cloud.
# Para persistência REAL, a versão com CSV ou DB externo deve ser usada, mas exige estabilidade que só um DB oferece.
# =========================================================
if 'respostas' not in st.session_state:
    st.session_state.respostas = pd.DataFrame(columns=[
        'Data', 'Nome', 'Whatsapp', 'Aniversario', 'Como_Conheceu', 'Segmento',
        'Nota_Atendimento', 'Nota_Qualidade_Sabor', 'Nota_Entrega_Ambiente',
        'NPS_Recomendacao', 'Comentario'
    ])
if 'como_conheceu_outro' not in st.session_state:
    st.session_state.como_conheceu_outro = ""
if 'show_form' not in st.session_state:
    st.session_state.show_form = True


# =========================================================
# INTERFACE DO FORMULÁRIO
# =========================================================
st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40seg.</p>", unsafe_allow_html=True)
st.markdown("---")

# Container para mostrar o formulário ou a mensagem de agradecimento
form_container = st.container()
mensagem_container = st.empty()


if st.session_state.show_form:
    with form_container:
        with st.form("pesquisa_form"):
            # Segmento
            segmento = st.radio(
                "**Onde foi sua experiência?**",
                options=["Restaurante (Salão)", "Delivery (Entrega)"],
                horizontal=True,
                key='seg_radio' # Chave única
            )
            st.markdown("---")

            # Dados pessoais
            col1, col2, col3 = st.columns(3)
            nome = col1.text_input("**Seu nome completo:**", key='nome_input')
            whatsapp = col2.text_input("**Seu WhatsApp:**", key='whats_input')
            aniversario = col3.date_input(
                "**Data de aniversário:**",
                value=datetime.today(),
                key='aniv_input'
            )

            # Como conheceu
            opcoes_conheceu_base = [
                "Instagram", "Facebook", "Google", "Indicação de amigo/familiar",
                "Passando em frente ao restaurante", "Placa na entrada de Schroeder (ponte)",
                "Outro:"
            ]
            if segmento == "Restaurante (Salão)":
                opcoes_conheceu = ["Já era cliente do delivery"] + opcoes_conheceu_base
            else:
                opcoes_conheceu = ["Já era cliente do salão"] + opcoes_conheceu_base

            como_conheceu = st.selectbox(
                "**Como você nos conheceu?**",
                ["Selecione uma opção"] + opcoes_conheceu,
                key='conheceu_select'
            )

            como_outro = ""
            if como_conheceu == "Outro:":
                como_outro = st.text_input("Como nos conheceu:", key='outro_input')
            
            st.markdown("---")

            # =========================================================
            # PERGUNTAS AVALIATIVAS
            # =========================================================
            opcoes = list(range(0, 11))

            if segmento == "Restaurante (Salão)":
                st.subheader("🍽️ Avaliação no Salão")
                nota_atendimento = st.radio("1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):", opcoes, horizontal=True, key='nota_atendimento_s')
                nota_qualidade = st.radio("2️⃣ Qualidade e sabor dos pratos:", opcoes, horizontal=True, key='nota_qualidade_s')
                nota_entrega_ambiente = st.radio("3️⃣ Ambiente e limpeza:", opcoes, horizontal=True, key='nota_ambiente_s')
                
                # Nulo para Delivery
                nota_pedido_embalagem_delivery = None 

            else:
                st.subheader("🛵 Avaliação do Delivery")
                nota_atendimento = st.radio("1️⃣ Atendimento e facilidade do pedido:", opcoes, horizontal=True, key='nota_atendimento_d')
                
                # Mudança de nome de variável para simplificar o armazenamento final
                nota_pedido_embalagem_delivery = st.radio("2️⃣ Logística (tempo e embalagem):", opcoes, horizontal=True, key='nota_embalagem_d')
                
                nota_qualidade = st.radio("3️⃣ Qualidade e sabor pós-entrega:", opcoes, horizontal=True, key='nota_qualidade_d')
                nota_entrega_ambiente = st.radio("4️⃣ Apresentação e cuidado com os itens:", opcoes, horizontal=True, key='nota_ambiente_d')
            
            # Pergunta NPS (Numerada corretamente)
            nps_recomendacao = st.radio("5️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?", opcoes, horizontal=True, key='nps_radio')
            
            st.markdown("---")

            comentario = st.text_area(
                "💬 Comentários, sugestões, elogios ou reclamações (opcional):",
                max_chars=500,
                key='comentario_input'
            )

            # 🚀 BOTÃO DE ENVIO (OBRIGATÓRIO)
            enviar = st.form_submit_button("Enviar Respostas ✅")
else:
    # Se o formulário não for mostrado, o botão de envio deve ser definido como False
    enviar = False


# =========================================================
# PROCESSAMENTO DE RESPOSTA
# =========================================================
if enviar:
    if not nome or not whatsapp or como_conheceu == "Selecione uma opção":
        st.error("⚠️ Por favor, preencha Nome, WhatsApp e Como nos conheceu.")
        # Se falhar na validação, forçamos o formulário a reaparecer
        st.session_state.show_form = True
    else:
        # Se for Salão, nota_pedido_embalagem_delivery deve ser None (e vice-versa)
        nota_embalagem_final = nota_pedido_embalagem_delivery if segmento == "Delivery (Entrega)" else None
        
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
            "Nota_Pedido_Embalagem": nota_embalagem_final, # Armazena corretamente
            "NPS_Recomendacao": nps_recomendacao,
            "Comentario": comentario
        }])
        
        # Armazena no Session State
        st.session_state.respostas = pd.concat([st.session_state.respostas, nova], ignore_index=True)
        
        # Oculta o formulário e mostra a mensagem de sucesso
        st.session_state.show_form = False
        form_container.empty()
        
        with mensagem_container:
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
                st.balloons()
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
            
            st.markdown("---")


# =========================================================
# ÁREA ADMINISTRATIVA (ACESSO VIA URL SECRETA)
# =========================================================
# Acessível via: SEU_APP_URL/?admin=SUA_SENHA_SECRETA
ADMIN_KEY = 'admin'
ADMIN_PASSWORD = 'pureto2025' # Sua senha secreta

query_params = st.query_params

if ADMIN_KEY in query_params and query_params[ADMIN_KEY] == ADMIN_PASSWORD:
    st.markdown("---")
    st.title("🔐 Dashboard Administrativo")
    st.subheader("Acesso liberado (apenas para o link secreto)")

    df_admin = st.session_state.respostas
    total_admin = len(df_admin)
    
    if total_admin > 0:
        nps_admin, prom, neut, det, total = calcular_nps(df_admin)
        
        col_nps, col_total = st.columns(2)
        col_nps.metric("NPS Score", f"{nps_admin:.1f}")
        col_total.metric("Total Respostas", total)

        # Download
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode("utf-8")

        csv = convert_df(df_admin)
        st.download_button(
            label="⬇️ Baixar Relatório Completo (CSV)",
            data=csv,
            file_name='relatorio_pesquisa_pureto.csv',
            mime='text/csv'
        )
        st.dataframe(df_admin.sort_values(by="Data", ascending=False), use_container_width=True)
    else:
        st.warning("Ainda não há respostas registradas nesta sessão.")
