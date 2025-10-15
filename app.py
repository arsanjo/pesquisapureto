import streamlit as st
import pandas as pd
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"
ADMIN_KEY = "admin"
ADMIN_PASSWORD = "pureto2025"
SUBMIT_KEY = 'pesquisa_enviada' 

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

@st.cache_data
def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

# Função para forçar o formato DD/MM/AAAA na string (para text_input)
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

# =========================================================
# TÍTULO E SEGMENTO
# =========================================================
st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40 segundos.</p>", unsafe_allow_html=True)
st.markdown("---")

segmento = st.radio("**Sua compra na Pureto foi?**", ["Restaurante (Salão)", "Delivery (Entrega)"], horizontal=True, key="segmento_selecionado")
st.markdown("---")

# =========================================================
# LÓGICA "COMO CONHECEU" (FORA DO FORM PARA RENDERIZAÇÃO IMEDIATA)
# =========================================================
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

# O widget Selectbox (precisa estar fora do form para atualização imediata)
como_conheceu = st.selectbox("Como nos conheceu?", opcoes_conheceu, key="conheceu_select")

# Campo "Outro:" Condicional
como_outro = ""
if como_conheceu == "Outro:":
    # Usamos st.session_state para este campo também, caso ele tenha sido preenchido
    if 'como_outro_input_value' not in st.session_state:
        st.session_state.como_outro_input_value = ""
    como_outro = st.text_input("Como nos conheceu? (Especifique):", value=st.session_state.como_outro_input_value, key="como_outro_input")
else:
    # Garante que o estado seja limpo se a opção for mudada, mas NÃO AQUI.
    como_outro = ""


# =========================================================
# FORMULÁRIO (Somente o que precisa ser enviado junto)
# =========================================================
if 'submit_status' in st.query_params and st.query_params['submit_status'] == 'success':
    submit = False 
else:
    with st.form("pesquisa_form"):
        st.subheader("Sobre você")
        col1, col2, col3 = st.columns(3)
        nome = col1.text_input("Seu nome completo:")
        whatsapp = col2.text_input("Seu WhatsApp:")
        
        # Data de aniversário (lê e salva o input no Session State para manter o valor)
        aniversario_raw = col3.text_input("Data de aniversário (DD/MM/AAAA):", value=st.session_state.aniversario_raw_value, placeholder="Ex: 14101972 (apenas números)", key="aniversario_raw_input")
        st.session_state.aniversario_raw_value = aniversario_raw 
        aniversario = formatar_data(aniversario_raw)

        # Visualização simples do Como Conheceu
        st.markdown(f"**Como nos conheceu:** {como_conheceu}{f' (Especificado: {como_outro})' if como_outro else ''}")
        
        st.markdown("---")
        opcoes = list(range(0, 11))
        
        # Inicializa as variáveis de nota para o escopo de envio
        nota_atend, nota_sabor, nota_ambiente, nota_embalagem, nps = 0, 0, 0, None, 0

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
        submit = st.form_submit_button("Enviar Respostas ✅")


# =========================================================
# PROCESSAMENTO E MENSAGENS 
# =========================================================
if 'submit_status' in st.query_params and st.query_params['submit_status'] == 'success':
    # Lógica de URL para exibir mensagens de sucesso (NÃO MEXEMOS AQUI)
    nome_sucesso = st.query_params.get('nome', [''])[0]
    nps_sucesso = int(st.query_params.get('nps', [0])[0])

    st.success("✅ Pesquisa enviada com sucesso!")
    
    # 1ª Mensagem: Cupom
    st.markdown(f"""
    <div style='background-color:#e8f5e9; color:#1b5e20; padding:20px; border-radius:10px; margin-top:20px;'>
    <h3>🎉 {nome_sucesso}, muito obrigado pelas suas respostas sinceras!</h3>
    <p>Seu feedback é essencial para aperfeiçoarmos cada detalhe do <b>Pureto Sushi</b>.</p>
    <p>Para agradecer, você ganhou um <b>cupom especial de 10% de desconto</b> na sua próxima compra.</p>
    <p style='font-size:1.2em;'><b>Use o código:</b> <span style='color:#007bff;'>PESQUISA</span></p>
    </div>
    """, unsafe_allow_html=True)

    # 2ª Mensagem: Google + Entrega Grátis
    if nps_sucesso >= 9:
        st.balloons()
        st.markdown(f"""
        <div style='background-color:#fff3cd; color:#856404; padding:20px; border-radius:10px; margin-top:25px;'>
        <h4 style='font-weight:bold;'>Google <span style='font-size:1.5em;'>⭐⭐⭐⭐⭐</span></h4>
        <p>{nome_sucesso}, e que tal compartilhar sua opinião lá no Google? Isso nos ajuda muito! 🙏</p>
        <p><b>Como gratidão, sua próxima entrega é grátis!</b></p>
        <a href='{GOOGLE_REVIEW_LINK}' target='_blank'
           style='background-color:#f0ad4e; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;'>
           💬 Avaliar no Google
        </a>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.info("Obrigado por contribuir!")
    
    # Limpa o parâmetro de sucesso após exibição para que o formulário apareça na próxima interação
    st.query_params.pop('submit_status')
    st.query_params.pop('nome')
    st.query_params.pop('nps')


elif submit:
    # Lógica de processamento e salvamento
    if not nome or not whatsapp or como_conheceu == "Selecione uma opção":
        st.error("⚠️ Por favor, preencha Nome, WhatsApp e Como nos conheceu.")
    elif aniversario and (aniversario == aniversario_raw or len(aniversario_raw) != 8):
        st.error("⚠️ Data de aniversário inválida. Por favor, use 8 dígitos (DDMMAAAA) ou preencha corretamente.")
    else:
        # 1. Criação do DataFrame
        como_conheceu_final = como_outro if como_conheceu == "Outro:" else como_conheceu
        
        nova = pd.DataFrame([{
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Nome": nome,
            "Whatsapp": whatsapp,
            "Aniversario": aniversario, # Valor já formatado
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

        # 🚨 CORREÇÃO PRINCIPAL: Resetar o estado dos campos antes do rerun
        st.session_state['conheceu_select'] = "Selecione uma opção" # Reset Selectbox (Funciona com o rerun)
        st.session_state['aniversario_raw_input'] = "" # Reset Data Input
        st.session_state['como_outro_input_value'] = "" # Reset Campo "Outro"
        
        # 2. Redirecionamento para a página de sucesso (com parâmetros)
        params = st.query_params.to_dict()
        params.update({
            'submit_status': 'success',
            'nome': nome,
            'nps': nps
        })
        st.query_params.update(params)
        st.rerun()


# =========================================================
# ADMIN (via URL ?admin=pureto2025)
# =========================================================
query = st.query_params
if ADMIN_KEY in query and query[ADMIN_KEY] == ADMIN_PASSWORD:
    st.markdown("---")
    st.title("🔐 Dashboard Administrativo")
    df = st.session_state.respostas
    if len(df) > 0:
        nps_admin, prom, neut, det, total = calcular_nps(df)
        col_nps, col_total = st.columns(2)
        col_nps.metric("NPS Score", f"{nps_admin:.1f}")
        col_total.metric("Total Respostas", total)
        
        csv = to_csv_bytes(df)
        st.download_button("📥 Baixar Respostas (CSV)", csv, "respostas_pesquisa.csv", "text/csv")
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
    else:
        st.warning("Ainda não há respostas coletadas.")
