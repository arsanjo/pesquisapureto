# app.py
import streamlit as st
import pandas as pd
from datetime import datetime

# =========================================================
# CONFIGURAÇÃO GERAL
# =========================================================
st.set_page_config(page_title="Pesquisa de Satisfação - Pureto Sushi", layout="wide")
GOOGLE_REVIEW_LINK = "https://g.page/puretosushi/review"

ADMIN_KEY = "admin"            # parâmetro na URL
ADMIN_PASSWORD = "pureto2025"  # valor esperado na URL (ex.: ?admin=pureto2025)

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def calcular_nps(df: pd.DataFrame):
    if df.empty or "NPS_Recomendacao" not in df.columns:
        return 0.0, 0.0, 0.0, 0.0, 0
    total = len(df)
    promotores = (df["NPS_Recomendacao"] >= 9).sum()
    detratores = (df["NPS_Recomendacao"] <= 6).sum()
    perc_prom = (promotores / total) * 100
    perc_det = (detratores / total) * 100
    perc_neut = 100 - perc_prom - perc_det
    nps_score = perc_prom - perc_det
    return nps_score, perc_prom, perc_neut, perc_det, total

@st.cache_data
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def valida_data_ddmmaa(texto: str) -> str:
    """Valida e retorna a data no formato DD/MM/AAAA. Lança ValueError se inválida."""
    data = datetime.strptime(texto.strip(), "%d/%m/%Y")
    return data.strftime("%d/%m/%Y")

# ---- Máscara automática para o campo de data (insere "/" ao digitar) ----
def mask_aniversario():
    raw = st.session_state.get("aniversario_txt", "")
    digits = "".join(ch for ch in raw if ch.isdigit())[:8]  # limita a 8 números (DDMMAAAA)

    out = ""
    if len(digits) >= 2:
        out = digits[:2] + "/"
    else:
        out = digits

    if len(digits) >= 4:
        out += digits[2:4] + "/"
    elif len(digits) > 2:
        out += digits[2:]

    if len(digits) > 4:
        out += digits[4:]

    # Evita piscar se já está igual
    if st.session_state["aniversario_txt"] != out:
        st.session_state["aniversario_txt"] = out

# =========================================================
# ESTADO INICIAL (BANCO EM MEMÓRIA)
# =========================================================
if "respostas" not in st.session_state:
    st.session_state.respostas = pd.DataFrame(
        columns=[
            "Data",
            "Nome",
            "Whatsapp",
            "Aniversario",
            "Como_Conheceu",
            "Segmento",
            "Nota_Atendimento",
            "Nota_Qualidade_Sabor",
            "Nota_Entrega_Ambiente",
            "Nota_Pedido_Embalagem",
            "NPS_Recomendacao",
            "Comentario",
        ]
    )

# =========================================================
# TÍTULO
# =========================================================
st.markdown("<h1 style='text-align:center;'>Pesquisa de Satisfação</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center;'>Sua opinião é muito importante para nós! Leva menos de 40 segundos.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# =========================================================
# FORMULÁRIO
# =========================================================
with st.form("pesquisa_form", clear_on_submit=False):
    # Segmento
    segmento = st.radio(
        "**Sua compra na Pureto foi?**",
        options=["Restaurante (Salão)", "Delivery (Entrega)"],
        horizontal=True,
        key="seg_radio",
    )
    st.markdown("---")

    # Dados pessoais
    st.subheader("Sobre você")
    col1, col2, col3 = st.columns(3)
    nome = col1.text_input("**Seu nome completo:**", key="nome_input")
    whatsapp = col2.text_input("**Seu WhatsApp:**", key="whats_input")

    # Campo de data com MÁSCARA automática (on_change -> insere "/")
    if "aniversario_txt" not in st.session_state:
        st.session_state["aniversario_txt"] = ""
    col3.text_input(
        "**Data de aniversário (DD/MM/AAAA):**",
        key="aniversario_txt",
        placeholder="Ex: 25/12/1990",
        on_change=mask_aniversario,
    )

    st.markdown("---")

    # Como nos conheceu (opções mudam por segmento)
    if segmento == "Restaurante (Salão)":
        opcoes_conheceu = [
            "Selecione uma opção",
            "Já era cliente do delivery",
            "Instagram",
            "Facebook",
            "Google",
            "Indicação de amigo/familiar",
            "Passando em frente ao restaurante",
            "Placa na entrada de Schroeder (ponte)",
            "Outro:",
        ]
    else:
        opcoes_conheceu = [
            "Selecione uma opção",
            "Já era cliente do salão",
            "Instagram",
            "Facebook",
            "Google",
            "Indicação de amigo/familiar",
            "Passando em frente ao restaurante",
            "Placa na entrada de Schroeder (ponte)",
            "Outro:",
        ]

    como_conheceu = st.selectbox("**Como nos conheceu?**", opcoes_conheceu, key="conheceu_select")

    # Campo "Outro" — SOMENTE quando "Outro:" for selecionado
    como_conheceu_outro = ""
    if como_conheceu == "Outro:":
        como_conheceu_outro = st.text_input("Como nos conheceu? (Especifique):", key="como_outro_input")

    st.markdown("---")

    # Perguntas (0 a 10) — com chaves distintas por segmento para não “vazar”
    opcoes_notas = list(range(0, 11))

    if segmento == "Restaurante (Salão)":
        st.subheader("🍽️ Avaliação do Salão")
        nota_atendimento = st.radio(
            "1️⃣ Atendimento da equipe (cortesia, agilidade e simpatia):",
            opcoes_notas,
            horizontal=True,
            key="nota_atendimento_s",
        )
        nota_qualidade_sabor = st.radio(
            "2️⃣ Qualidade e sabor dos pratos:",
            opcoes_notas,
            horizontal=True,
            key="nota_qualidade_s",
        )
        nota_entrega_ambiente = st.radio(
            "3️⃣ Ambiente e limpeza:",
            opcoes_notas,
            horizontal=True,
            key="nota_ambiente_s",
        )
        nota_pedido_embalagem = None  # não se aplica ao salão
        nps = st.radio(
            "4️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?",
            opcoes_notas,
            horizontal=True,
            key="nps_s",
        )
    else:
        st.subheader("🛵 Avaliação do Delivery")
        nota_atendimento = st.radio(
            "1️⃣ Atendimento e facilidade do pedido:",
            opcoes_notas,
            horizontal=True,
            key="nota_atendimento_d",
        )
        nota_pedido_embalagem = st.radio(
            "2️⃣ Logística (tempo e embalagem):",
            opcoes_notas,
            horizontal=True,
            key="nota_embalagem_d",
        )
        nota_qualidade_sabor = st.radio(
            "3️⃣ Qualidade e sabor pós-entrega:",
            opcoes_notas,
            horizontal=True,
            key="nota_qualidade_d",
        )
        nota_entrega_ambiente = st.radio(
            "4️⃣ Apresentação e cuidado com os itens:",
            opcoes_notas,
            horizontal=True,
            key="nota_ambiente_d",
        )
        nps = st.radio(
            "5️⃣ Em uma escala de 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?",
            opcoes_notas,
            horizontal=True,
            key="nps_d",
        )

    st.markdown("---")

    comentario = st.text_area(
        "💬 Comentários, sugestões, elogios ou reclamações (opcional):",
        max_chars=500,
        key="comentario_input",
    )

    enviar = st.form_submit_button("Enviar Respostas ✅")

# =========================================================
# PROCESSAMENTO
# =========================================================
if enviar:
    # Valida campos obrigatórios
    if not nome or not whatsapp or como_conheceu == "Selecione uma opção":
        st.error("⚠️ Por favor, preencha Nome, WhatsApp e Como nos conheceu.")
        st.stop()

    # Valida/normaliza data (opcional, mas se preenchida precisa ser válida)
    aniversario_fmt = ""
    if st.session_state["aniversario_txt"].strip():
        try:
            aniversario_fmt = valida_data_ddmmaa(st.session_state["aniversario_txt"])
        except ValueError:
            st.warning("⚠️ Data inválida. Use o formato DD/MM/AAAA (ex: 14/10/2025).")
            st.stop()

    # Resolve valor final de "Como_Conheceu"
    como_final = como_conheceu_outro if como_conheceu == "Outro:" else como_conheceu

    # Nova linha
    nova = pd.DataFrame(
        [
            {
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Nome": nome,
                "Whatsapp": whatsapp,
                "Aniversario": aniversario_fmt,
                "Como_Conheceu": como_final,
                "Segmento": segmento,
                "Nota_Atendimento": nota_atendimento,
                "Nota_Qualidade_Sabor": nota_qualidade_sabor,
                "Nota_Entrega_Ambiente": nota_entrega_ambiente,
                "Nota_Pedido_Embalagem": nota_pedido_embalagem,
                "NPS_Recomendacao": nps,
                "Comentario": comentario,
            }
        ]
    )

    st.session_state.respostas = pd.concat([st.session_state.respostas, nova], ignore_index=True)

    # Mensagens de agradecimento (agora aparecem sempre que envia)
    st.success("✅ Pesquisa enviada com sucesso!")
    st.markdown(
        f"""
        <div style='background-color:#e8f5e9; color:#1b5e20; padding:20px; border-radius:10px; margin-top:20px;'>
            <h3>🎉 {nome}, muito obrigado pelas suas respostas sinceras!</h3>
            <p>Seu feedback é essencial para aperfeiçoarmos cada detalhe do <b>Pureto Sushi</b>.</p>
            <p>Para agradecer, você ganhou um <b>cupom especial de 10% de desconto</b> na sua próxima compra.</p>
            <p style='font-size:1.2em;'><b>Use o código:</b> <span style='color:#007bff;'>PESQUISA</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if nps >= 9:
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
            """,
            unsafe_allow_html=True,
        )

    st.info("✅ Suas respostas foram registradas com sucesso. Obrigado por contribuir!")

# =========================================================
# ÁREA ADMINISTRATIVA (ACESSO POR URL SECRETA)
# Exemplo: http://localhost:8501/?admin=pureto2025
# =========================================================
query = st.query_params  # Streamlit 1.31+
if ADMIN_KEY in query and query[ADMIN_KEY] == ADMIN_PASSWORD:
    st.markdown("---")
    st.title("🔐 Dashboard Administrativo")
    st.caption("Acesso liberado (link com parâmetro secreto).")

    df = st.session_state.respostas.copy()
    total = len(df)

    if total == 0:
        st.warning("Ainda não há respostas registradas.")
    else:
        nps_score, prom, neut, det, total_calc = calcular_nps(df)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("NPS", f"{nps_score:.1f}")
        c2.metric("Promotores (%)", f"{prom:.1f}")
        c3.metric("Neutros (%)", f"{neut:.1f}")
        c4.metric("Detratores (%)", f"{det:.1f}")
        c5.metric("Total", f"{total_calc}")

        st.download_button(
            "⬇️ Baixar relatório (CSV)",
            data=to_csv_bytes(df),
            file_name="relatorio_pesquisa_pureto.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
