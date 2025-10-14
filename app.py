import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# CONFIGURAÇÕES INICIAIS E CONEXÃO COM GOOGLE SHEETS
# ============================================================
st.set_page_config(page_title="Pesquisa de Satisfação — Pureto", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"

# Definir o escopo de permissões (COM A CORREÇÃO)
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scopes
)
client = gspread.authorize(creds)

# Abrir a planilha pelo nome definido nos Secrets
sheet_name = st.secrets["google_sheet"]["sheet_name"]
spreadsheet = client.open(sheet_name)
worksheet = spreadsheet.worksheet(spreadsheet.worksheets()[0].title)

# ============================================================
# FUNÇÕES DE DADOS E CÁLCULO
# ============================================================
def read_data():
    """Lê os dados da planilha e retorna como DataFrame."""
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)

def write_data(df_row):
    """Escreve uma nova linha de dados na planilha."""
    values = df_row.values.tolist()[0]
    worksheet.append_row(values, value_input_option="USER_ENTERED")

def calcular_nps(df):
    """Calcula o NPS a partir de um DataFrame."""
    if df.empty or "NPS" not in df.columns or df["NPS"].isnull().all():
        return 0, 0
    total = len(df)
    promotores = df[df["NPS"] >= 9].shape[0]
    detratores = df[df["NPS"] <= 6].shape[0]
    nps_score = ((promotores - detratores) / total) * 100
    return nps_score, total

# ============================================================
# ROTEAMENTO: ADMIN vs CLIENTE
# ============================================================
query_params = st.query_params

# --- VISÃO DO ADMINISTRADOR ---
if "admin" in query_params and query_params["admin"] == "1":
    st.title("🔒 Painel Administrativo de Respostas")
    st.markdown("Resultados coletados da pesquisa de satisfação, lidos diretamente da Planilha Google.")
    
    try:
        df = read_data()
        
        if not df.empty:
            nps_geral, total_respostas = calcular_nps(df)
            
            col1, col2 = st.columns(2)
            col1.metric("NPS Geral", f"{nps_geral:.1f}")
            col2.metric("Total de Respostas", total_respostas)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar Todas as Respostas (CSV)",
                data=csv,
                file_name="respostas_pesquisa_pureto.csv",
                mime="text/csv",
            )
            
            st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
            
        else:
            st.info("Nenhuma resposta foi coletada ainda na Planilha Google.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao tentar ler a planilha: {e}")
        st.info("Verifique se as permissões da planilha e os 'Secrets' do Streamlit estão configurados corretamente.")

# --- VISÃO DO CLIENTE (FORMULÁRIO) ---
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

        else: # Delivery
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
            with st.spinner("Enviando sua resposta..."):
                como_conheceu_final = como_conheceu
                if como_conheceu == "Outro" and como_conheceu_outro:
                    como_conheceu_final = f"Outro: {como_conheceu_outro}"

                aniversario_str = aniversario.strftime("%d/%m/%Y")
                
                nova_resposta_df = pd.DataFrame([{
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Nome": nome, "Whatsapp": whatsapp,
                    "Aniversario": aniversario_str, "Como_Conheceu": como_conheceu_final, "Segmento": segmento,
                    "Nota1": nota1, "Nota2": nota2, "Nota3": nota3, "Nota4": nota4, "Nota5": nota5,
                    "NPS": nps, "Comentario": comentario
                }])

                write_data(nova_resposta_df)

            st.success(f"{nome}, sua avaliação foi registrada com sucesso!")
            st.markdown("""
            <div style='background-color:#e8f5e9;padding:20px;border-radius:10px;text-align:center;'>
            <h4>Seu feedback é essencial para melhorarmos sempre! 🍣</h4>
            <p>Como agradecimento, use o cupom <b>PESQUISA10</b> e ganhe <b>10% de desconto</b>.</p>
            </div>
            """, unsafe_allow_html=True)
            if nps >= 9:
                st.balloons()
                st.markdown(f"""
                <div style='background-color:#fff3cd;padding:20px;border-radius:10px;margin-top:20px;text-align:center;'>
                <h4>🌟 {nome}, sua opinião positiva vale ouro!</h4>
                <p>Que tal compartilhá-la no Google? Isso nos ajuda imensamente a crescer.</p>
                <a href='{GOOGLE_REVIEW_LINK}' target='_blank' style='display:inline-block; background:#f0ad4e;color:white;padding:12px 25px;border-radius:5px;text-decoration:none;font-weight:bold;'>Deixar Avaliação no Google</a>
                </div>
                """, unsafe_allow_html=True)

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("""
<hr style="margin-top: 50px;">
<div style='text-align:center; color:gray; font-size: 0.9em;'>
    <i>"Somos mais do que vencedores." — Romanos 8:37</i>
    <br>
    Desenvolvido por <b>Arsanjo</b>
</div>
""", unsafe_allow_html=True)
