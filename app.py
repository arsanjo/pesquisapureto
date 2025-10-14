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
# Variável para o campo 'Outro:'
if 'como_conheceu_outro_temp' not in st.session_state:
    st.session_state.como_conheceu_outro_temp = ""

# =========================================================
# INTERFACE DO FORMULÁRIO
# =========================================================
st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40 segundos.</p>", unsafe_allow_html=True) 
st.markdown("---")

# Variáveis para o escopo de envio, inicializadas fora do form
nota_atendimento = 0
nota_qualidade_sabor = 0
nota_ambiente_logistica = 0
nota_pedido_embalagem_delivery = None
nps_recomendacao = 0
opcoes_notas = list(range(0, 11))


with st.form("pesquisa_form"):
    
    # 2. SELEÇÃO DO SEGMENTO
    segmento = st.radio(
        "**Sua compra na Pureto foi?**", 
        options=["Restaurante (Salão)", "Delivery (Entrega)"],
        horizontal=True,
        key='seg_radio'
    )
    st.markdown("---")

    # 1. DADOS DE IDENTIFICAÇÃO (FIXOS)
    st.subheader("Sobre você")
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("**Seu nome completo:**", key='nome_input')
    whatsapp = col2.text_input("**Seu WhatsApp:**", key='whats_input')
    
    # Data de Aniversário (DD/MM/AAAA garantido no salvamento)
    aniversario = col3.date_input(
        "**Data de aniversário (DD/MM/AAAA):**",
        value=datetime.today().date(), 
        min_value=datetime(1900, 1, 1).date(),
        max_value=datetime.today().date(),
        key='aniv_input'
    )

    # Lógica Como Conheceu
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
        "**Como nos conheceu?**",
        ["Selecione uma opção"] + opcoes_conheceu,
        key='conheceu_select'
    )

    # 🚨 CORREÇÃO LÓGICA "OUTRO:": Exibe o campo de texto condicionalmente
    if como_conheceu == "Outro:":
        st.session_state.como_conheceu_outro_temp = st.text_input("Como nos conheceu? (Especifique):", key='outro_input')
    else:
        st.session_state.como_conheceu_outro_temp = ""
    
    st.markdown("---")

    # =========================================================
    # PERGUNTAS AVALIATIVAS (Lógica de exibição CORRIGIDA)
    # =========================================================
    
    if segmento == "Restaurante (Salão)":
        st.subheader("🍽️ Avaliação no Salão")
        nota_atendimento = st.radio("1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):", opcoes_notas, horizontal=True, key='nota_atendimento_s')
        nota_qualidade_sabor = st.radio("2️⃣ Qualidade e sabor dos pratos:", opcoes_notas, horizontal=True, key='nota_qualidade_s')
        nota_ambiente_logistica = st.radio("3️⃣ Ambiente e limpeza:", opcoes_notas, horizontal=True, key='nota_ambiente_s')
        
        nota_pedido_embalagem_delivery = None # Nulo para Salão
        nps_recomendacao = st.radio("4️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?", opcoes_notas, horizontal=True, key='nps_radio_s')

    else: # Delivery (Entrega)
        st.subheader("🛵 Avaliação do Delivery")
        nota_atendimento = st.radio("1️⃣ Atendimento e facilidade do pedido:", opcoes_notas, horizontal=True, key='nota_atendimento_d')
        
        nota_pedido_embalagem_delivery = st.radio("2️⃣ Logística (tempo e embalagem):", opcoes_notas, horizontal=True, key='nota_embalagem_d')
        
        nota_qualidade_sabor = st.radio("3️⃣ Qualidade e sabor pós-entrega:", opcoes_notas, horizontal=True, key='nota_qualidade_d')
        nota_ambiente_logistica = st.radio("4️⃣ Apresentação e cuidado com os itens:", opcoes_notas, horizontal=True, key='nota_ambiente_d')
        
        nps_recomendacao = st.radio("5️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?", opcoes_notas, horizontal=True, key='nps_radio_d')
    
    st.markdown("---")

    comentario = st.text_area(
        "💬 Comentários, sugestões, elogios ou reclamações (opcional):",
        max_chars=500,
        key='comentario_input'
    )

    enviar = st.form_submit_button("Enviar Respostas ✅")

# =========================================================
# PROCESSAMENTO DE RESPOSTA
# =========================================================
if enviar:
    # 1. Validação
    if not nome or not whatsapp or como_conheceu == "Selecione uma opção":
        st.error("⚠️ Por favor, preencha Nome, WhatsApp e Como nos conheceu.")
        # Mantém a execução para que o formulário permaneça com os dados preenchidos
    else:
        # 2. Processamento e Armazenamento
        
        # GARANTIA DA DATA DD/MM/AAAA NO SALVAMENTO
        aniversario_str = aniversario.strftime("%d/%m/%Y") 
        como_final = st.session_state.como_conheceu_outro_temp if como_conheceu == "Outro:" else como_conheceu

        nova = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Nome": nome,
            "Whatsapp": whatsapp,
            "Aniversario": aniversario_str,
            "Como_Conheceu": como_final,
            "Segmento": segmento,
            "Nota_Atendimento": nota_atendimento,
            "Nota_Qualidade_Sabor": nota_qualidade_sabor,
            "Nota_Entrega_Ambiente": nota_ambiente_logistica,
            "Nota_Pedido_Embalagem": nota_pedido_embalagem_delivery,
            "NPS_Recomendacao": nps_recomendacao,
            "Comentario": comentario
        }])
        
        st.session_state.respostas = pd.concat([st.session_state.respostas, nova], ignore_index=True)
        
        # 3. Exibição das Mensagens e Agradecimento
        
        # Limpa a tela e mostra as mensagens no topo
        st.empty() 
        
        st.success("✅ Pesquisa enviada com sucesso!")
        
        # ✅ Mensagem padrão (Cupom)
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

        # ⭐ Mensagem condicional (Google + Entrega Grátis)
        if nps_recomendacao > 8:
            st.balloons()
            st.markdown(
                f"""
                <div style='background-color:#fff3cd; color:#856404; padding:20px; border-radius:10px; margin-top:25px;'>
                    <h4 style='font-weight:bold; color:#856404;'>Google <span style='font-size:1.5em;'>⭐⭐⭐⭐⭐</span></h4>
                    <p>{nome}, e que tal compartilhá-la essa sua incrível opinião lá no Google com um comentário positivo? Isso nos ajuda muito! 🙏</p>
                    <p style='font-weight:bold;'>Como gratidão por essa parte, sua próxima entrega é grátis.</p>
                    <a href='{GOOGLE_REVIEW_LINK}' target='_blank'
                    style='background-color:#f0ad4e; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;'>
                        💬 Avaliar no Google
                    </a>
                </div>
                """, unsafe_allow_html=True
            )
        
        st.markdown("---")
        st.info("✅ Suas respostas foram registradas com sucesso. Obrigado por contribuir!")
        
        # Força o reinício para limpar a tela e prepara o próximo uso
        st.rerun() 

# =========================================================
# ÁREA ADMINISTRATIVA (ACESSO VIA URL SECRETA)
# =========================================================
ADMIN_KEY = 'admin'
ADMIN_PASSWORD = 'pureto2025' 
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
