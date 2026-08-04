import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
from supabase import create_client, Client
import google.generativeai as genai
import extra_streamlit_components as stx
from fpdf import FPDF

# ========================================================
# 1. CREDENCIAIS BASE
# ========================================================
SUPABASE_URL = "https://tlrrauzylknuatajzniu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRscnJhdXp5bGtudWF0YWp6bml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1MDE5ODMsImV4cCI6MjA5NjA3Nzk4M30.WiTNExA0hJY0AmDY794F7O0ft2SngctNoWQ_LBwyGDk"

try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except:
    GEMINI_API_KEY = ""

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

if GEMINI_API_KEY and GEMINI_API_KEY.strip() != "":
    genai.configure(api_key=GEMINI_API_KEY)
    modelo_ia = genai.GenerativeModel('gemini-1.0-pro')
else:
    modelo_ia = None

# ========================================================
# 2. CONFIGURAÇÃO VISUAL E CSS (ESTILO BI)
# ========================================================
st.set_page_config(page_title="Fluxo Financeiro PRO", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { font-family: 'Plus Jakarta Sans', sans-serif !important; background-color: #F3F4F6 !important; color: #0F172A !important; }
        h1, h2, h3, h4 { font-weight: 800 !important; letter-spacing: -0.5px !important; color: #1E293B !important; }
        .title-gradient { background: linear-gradient(90deg, #0284C7 0%, #4F46E5 50%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding-bottom: 10px; }
        div[data-baseweb="input"], .stSelectbox div { border-radius: 6px !important; }
        div.stButton > button[kind="primary"] { background: linear-gradient(90deg, #0284C7 0%, #4F46E5 100%) !important; border: none !important; color: white !important; font-weight: bold; border-radius: 6px; padding: 10px; }
        
        /* Estilo Power BI para os Cards */
        [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 800 !important; }
        [data-testid="stMetricLabel"] { font-size: 14px !important; font-weight: 600 !important; color: #64748B !important; }
        div[data-testid="metric-container"] { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
        
        .executive-box { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 15px; }
        hr { margin-top: 20px; margin-bottom: 20px; border: 0; border-top: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. AUTENTICAÇÃO COM FORÇA DE IDENTIDADE (CORREÇÃO DE NOME)
# ========================================================
if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_nome" not in st.session_state: st.session_state.user_nome = "Usuário"

cookie_manager = stx.CookieManager(key="auth_cookies_v5")
cookies = cookie_manager.get_all()

if st.session_state.user_email is None and cookies and "u_mail" in cookies and cookies["u_mail"]:
    st.session_state.user_email = cookies["u_mail"]
    # FORÇA A BUSCA DO NOME REAL NO SUPABASE
    try:
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            st.session_state.user_nome = user_res.user.user_metadata.get("primeiro_nome", cookies.get("u_name", "Usuário"))
    except:
        st.session_state.user_nome = cookies.get("u_name", "Usuário")

if not st.session_state.user_email:
    st.markdown("<h1 class='title-gradient' style='text-align: center; margin-top: 50px;'>Fluxo Financeiro PRO</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            aba_login, aba_registro = st.tabs(["🔒 Entrar", "✨ Criar Conta"])
            with aba_login:
                email_login = st.text_input("E-mail corporativo ou pessoal", key="log_email")
                senha_login = st.text_input("Senha de acesso", type="password", key="log_senha")
                if st.button("Acessar Painel", type="primary", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email_login, "password": senha_login})
                        st.session_state.user_email = res.user.email
                        nome_salvo = res.user.user_metadata.get("primeiro_nome", "Usuário")
                        st.session_state.user_nome = nome_salvo
                        cookie_manager.set("u_mail", res.user.email, max_age=30*24*60*60)
                        cookie_manager.set("u_name", nome_salvo, max_age=30*24*60*60)
                        st.rerun()
                    except Exception as e: st.error(f"Erro no login: {e}")
            with aba_registro:
                nome_reg = st.text_input("Seu primeiro nome:", key="reg_nome")
                email_reg = st.text_input("Seu e-mail:", key="reg_email")
                senha_reg = st.text_input("Crie uma Senha Forte:", type="password", key="reg_senha")
                if st.button("Garantir Acesso", type="primary", use_container_width=True):
                    if nome_reg.strip() and email_reg.strip():
                        try:
                            supabase.auth.sign_up({"email": email_reg, "password": senha_reg, "options": {"data": {"primeiro_nome": nome_reg.strip()}}})
                            st.success(f"Conta de {nome_reg} criada! Faça login.")
                        except Exception as e: st.error(f"Erro: {e}")
    st.stop()

# ========================================================
# 4. GESTÃO DE MASTER DATA (CADASTROS RESGATADOS)
# ========================================================
LISTA_RESP_BASE = [st.session_state.user_nome, "Família", "Empresa"]
LISTA_BANC_BASE = ["Banco do Brasil", "Inter", "Nubank", "Itaú", "Bradesco", "PicPay", "Mercado Pago"]
LISTA_CAT_DESP = ["Alimentação", "Transporte", "Moradia", "Salário", "Assinaturas", "Saúde", "Impostos", "Outros"]
LISTA_CAT_REC = ["Salário / Pró-Labore", "Rendimentos (Dividendos / JCP)", "Vendas", "Outros"]
LISTA_CAT_INV = ["Ações (B3)", "Fundos Imobiliários (FIIs)", "Renda Fixa", "Criptomoedas", "Ações (EUA)"]
LISTA_ORIG_BASE = ["Supermercado", "Pix", "Empresa", "Cliente"]

@st.cache_data(ttl=5)
def carregar_dados_completos(email):
    try:
        res = supabase.table("lancamentos").select("*").eq("user_email", email).execute()
        if res.data:
            df_t = pd.DataFrame(res.data)
            if "mes_pagamento" not in df_t.columns: df_t["mes_pagamento"] = df_t["competencia"]
            df_t["mes_pagamento"] = df_t["mes_pagamento"].fillna(df_t["competencia"])
            df_t = df_t.rename(columns={"id": "ID", "data_compra": "Data", "competencia": "Competencia", "mes_pagamento": "Mes_Pagamento", "tipo": "Tipo", "categoria": "Categoria", "subcategoria": "Subcategoria", "conta_cartao": "Conta_Cartao", "valor": "Valor", "descricao": "Descricao", "parcela": "Parcela", "responsavel": "Responsavel", "status": "Status", "origem_destino": "Origem_Destino"})
            df_t["Valor"] = pd.to_numeric(df_t["Valor"]).fillna(0.0)
            return df_t
    except: pass
    return pd.DataFrame(columns=["ID", "Data", "Mes_Pagamento", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status", "Origem_Destino"])

df_tudo = carregar_dados_completos(st.session_state.user_email)
df_configs = df_tudo[df_tudo["Tipo"].str.startswith("Config_")].copy() if not df_tudo.empty else pd.DataFrame(columns=df_tudo.columns)
df = df_tudo[~df_tudo["Tipo"].str.startswith("Config_")].copy() if not df_tudo.empty else pd.DataFrame(columns=df_tudo.columns)
df_cartoes = df_configs[df_configs["Tipo"] == "Config_Cartao"]

def obter_opcoes(coluna, lista_base):
    # Pega cadastros configurados
    configs = df_configs[df_configs["Tipo"] == f"Config_{coluna}"][coluna].dropna().astype(str).unique().tolist() if not df_configs.empty and coluna in df_configs.columns else []
    # Pega itens de lançamentos passados
    existentes = df[coluna].dropna().astype(str).unique().tolist() if not df.empty and coluna in df.columns else []
    # Pega lista negra
    ocultos = df_configs[(df_configs["Tipo"] == "Config_Excluida") & (df_configs["Categoria"] == coluna)]["Subcategoria"].dropna().astype(str).unique().tolist() if not df_configs.empty else []
    
    todos = set(lista_base + configs + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])
    for item in ocultos:
        if item in todos: todos.remove(item)
    return sorted(list(todos))

# ========================================================
# 5. HEADER (PADRÃO PROFISSIONAL)
# ========================================================
c_head1, c_head2 = st.columns([4, 1])
with c_head1: st.markdown("<h2 class='title-gradient'>Fluxo Financeiro PRO</h2>", unsafe_allow_html=True)
with c_head2:
    st.markdown(f"<div style='text-align: right; padding-top: 15px;'><span style='font-size:18px;'>👤 Olá, <b>{st.session_state.user_nome}</b></span></div>", unsafe_allow_html=True)
    if st.button("Sair (Logout)", use_container_width=True):
        cookie_manager.set("u_mail", "", max_age=-1)
        cookie_manager.set("u_name", "", max_age=-1)
        st.session_state.clear()
        st.rerun()

aba_dashboard, aba_lancamentos, aba_cadastros, aba_assistente = st.tabs(["📊 Visão BI & Gorila", "📝 Lançamentos Inteligentes", "⚙️ Central de Cadastros", "🤖 Assistente IA"])

# ========================================================
# 6. DASHBOARD: ESTILO POWER BI E GORILA
# ========================================================
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        dash_bi, dash_gorila, dash_faturas = st.tabs(["📊 Visão Global (BI)", "📈 Carteira de Investimentos (Gorila)", "💳 Gestão de Faturas"])
        
        with dash_bi:
            st.markdown("#### 🎯 Filtros Globais")
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1: 
                visao_caixa = st.toggle("Ativar Visão por Pagamento/Fatura (Regime de Caixa)", value=True)
                col_filtro = "Mes_Pagamento" if visao_caixa else "Competencia"
            with c_f2:
                meses_disp = sorted(df[col_filtro].dropna().unique(), reverse=True)
                mes_sel = st.selectbox("Período de Análise:", ["Ver Tudo"] + meses_disp)
            with c_f3:
                resp_sel = st.multiselect("Filtrar por Responsável:", obter_opcoes("Responsavel", LISTA_RESP_BASE), default=obter_opcoes("Responsavel", LISTA_RESP_BASE))
            
            df_dash = df.copy()
            if mes_sel != "Ver Tudo": df_dash = df_dash[df_dash[col_filtro] == mes_sel]
            if resp_sel: df_dash = df_dash[df_dash["Responsavel"].isin(resp_sel)]
            else: df_dash = df_dash.iloc[0:0]
            
            t_rec = df_dash[(df_dash["Tipo"] == "Receita") & (df_dash["Status"] == "Pago")]["Valor"].sum()
            t_desp = df_dash[(df_dash["Tipo"] == "Despesa") & (df_dash["Status"] == "Pago")]["Valor"].sum()
            t_inv = df_dash[df_dash["Tipo"] == "Investimento"]["Valor"].sum()
            saldo = t_rec - t_desp
            
            st.markdown("<br>", unsafe_allow_html=True)
            # UTILIZANDO OS CARDS NATIVOS ESTILO POWER BI
            cm1, cm2, cm3, cm4 = st.columns(4)
            cm1.metric(label="Saldo do Período", value=f"R$ {saldo:,.2f}", delta="Lucro" if saldo >= 0 else "Prejuízo", delta_color="normal")
            cm2.metric(label="Total Entradas", value=f"R$ {t_rec:,.2f}", delta="Receitas Líquidas")
            cm3.metric(label="Total Saídas", value=f"R$ {t_desp:,.2f}", delta="Despesas Pagas", delta_color="inverse")
            cm4.metric(label="Total Investido", value=f"R$ {t_inv:,.2f}", delta="Aportes e Alocações", delta_color="off")
            
            st.markdown("---")
            if t_desp > 0:
                cg1, cg2 = st.columns(2)
                with cg1: 
                    st.plotly_chart(px.pie(df_dash[df_dash["Tipo"] == "Despesa"], values="Valor", names="Categoria", title="Distribuição de Despesas (Onde seu dinheiro foi?)", hole=0.4), use_container_width=True)
                with cg2: 
                    st.plotly_chart(px.bar(df_dash[df_dash["Tipo"] == "Despesa"].groupby("Descricao")["Valor"].sum().reset_index().sort_values("Valor").tail(5), x="Valor", y="Descricao", orientation='h', title="Top 5 Maiores Gastos"), use_container_width=True)

        with dash_gorila:
            st.markdown("### 📈 Sua Carteira de Ativos")
            df_invest = df[df["Tipo"] == "Investimento"].copy()
            df_prov = df[(df["Tipo"] == "Receita") & (df["Categoria"].str.contains("Dividendos|JCP|Rendimentos", case=False, na=False))].copy()
            
            if not df_invest.empty:
                t_aportado = df_invest["Valor"].sum()
                t_proventos = df_prov["Valor"].sum() if not df_prov.empty else 0.0
                
                cp1, cp2, cp3 = st.columns(3)
                cp1.metric(label="Total Aportado Histórico", value=f"R$ {t_aportado:,.2f}")
                cp2.metric(label="Proventos Recebidos (JCP/Div)", value=f"R$ {t_proventos:,.2f}", delta="Cashback na Conta")
                cp3.metric(label="Ativos na Carteira", value=f"{df_invest['Subcategoria'].nunique()} tickers")
                
                st.markdown("<br>", unsafe_allow_html=True)
                ca1, ca2 = st.columns(2)
                with ca1:
                    df_grupo_ativos = df_invest.groupby("Subcategoria")["Valor"].sum().reset_index()
                    st.plotly_chart(px.pie(df_grupo_ativos, values="Valor", names="Subcategoria", title="Alocação por Ativo", hole=0.4), use_container_width=True)
                with ca2:
                    df_grupo_classe = df_invest.groupby("Categoria")["Valor"].sum().reset_index()
                    st.plotly_chart(px.bar(df_grupo_classe, x="Categoria", y="Valor", title="Alocação por Classe de Investimento", color="Categoria"), use_container_width=True)
                
                st.markdown("#### Extrato de Aportes")
                st.dataframe(df_invest[["Data", "Categoria", "Subcategoria", "Origem_Destino", "Valor"]].rename(columns={"Subcategoria": "Ticker", "Origem_Destino": "Corretora"}), use_container_width=True, hide_index=True)
            else:
                st.info("Você ainda não registrou nenhum Investimento. Use a aba de Lançamentos para criar seu portfólio.")
                
        with dash_faturas:
            st.markdown("### 💳 Mapa de Faturas (Contas a Pagar)")
            meses_fat = sorted(df["Mes_Pagamento"].dropna().unique(), reverse=True)
            if meses_fat:
                mf_sel = st.selectbox("Selecione o Vencimento:", meses_fat)
                df_fat = df[(df["Mes_Pagamento"] == mf_sel) & (df["Tipo"] == "Despesa")]
                cartoes = df_cartoes["Conta_Cartao"].unique().tolist() if not df_cartoes.empty else []
                df_apenas_cartoes = df_fat[df_fat["Conta_Cartao"].isin(cartoes)]
                
                if not df_apenas_cartoes.empty:
                    st.plotly_chart(px.bar(df_apenas_cartoes.groupby("Conta_Cartao")["Valor"].sum().reset_index().sort_values("Valor"), x="Valor", y="Conta_Cartao", orientation='h', title=f"Faturas de {mf_sel}", color_discrete_sequence=["#EF4444"]), use_container_width=True)
                    st.dataframe(df_apenas_cartoes[["Data", "Conta_Cartao", "Descricao", "Parcela", "Valor"]], use_container_width=True, hide_index=True)
                else: st.info("Sem despesas de cartão neste mês.")
    else: st.info("O Dashboard aguarda lançamentos.")

# ========================================================
# 7. LANÇAMENTOS INTELIGENTES (A MAGIA DE MERCADO)
# ========================================================
def auto_salvar_cadastro(tipo_cad, valor):
    try: supabase.table("lancamentos").insert({"user_email": st.session_state.user_email, "data_compra": datetime.now().strftime("%Y-%m-%d"), "competencia": datetime.now().strftime("%Y-%m"), "mes_pagamento": datetime.now().strftime("%Y-%m"), "tipo": f"Config_{tipo_cad}", "categoria": valor if tipo_cad == "Categoria" else "", "subcategoria": valor if tipo_cad == "Subcategoria" else "", "responsavel": valor if tipo_cad == "Responsavel" else "", "origem_destino": valor if tipo_cad == "Origem_Destino" else "", "conta_cartao": "", "valor": 0.0, "descricao": "Configuração Automática", "parcela": "-", "status": "Config"}).execute()
    except: pass

with aba_lancamentos:
    aba_manual, aba_gerenciar = st.tabs(["✍️ Painel de Lançamento", "✏️ Editar Histórico"])
    
    with aba_manual:
        # 1. ESCOLHA DO TIPO (O GATILHO MUTANTE)
        with st.container(border=True):
            c_tipo, c_val, c_data = st.columns(3)
            with c_tipo: tipo_mov = st.selectbox("O que vamos lançar hoje?", ["Despesa", "Receita", "Investimento"])
            with c_val: valor_total = st.number_input("Qual o Valor (R$)?", min_value=0.0, format="%.2f")
            with c_data: data_ocorreu = st.date_input("Qual a Data?")

        with st.container(border=True):
            st.markdown(f"#### Detalhes: {tipo_mov}")
            
            # ----------------------------------------------------
            # FORMULÁRIO DE DESPESA (Completo)
            # ----------------------------------------------------
            if tipo_mov == "Despesa":
                c4, c5, c6 = st.columns(3)
                with c4: 
                    cat_sel = st.selectbox("Categoria do Gasto", obter_opcoes("Categoria", LISTA_CAT_DESP) + ["➕ Nova..."])
                    categoria = st.text_input("Nova Categoria:") if cat_sel == "➕ Nova..." else cat_sel
                with c5:
                    conta_sel = st.selectbox("Cartão ou Conta Usada", ["Conta Corrente", "Pix", "Dinheiro Físico"] + (df_cartoes["Conta_Cartao"].unique().tolist() if not df_cartoes.empty else []) + ["➕ Novo Cartão/Conta..."])
                    conta_cartao = st.text_input("Nova Conta:") if conta_sel == "➕ Novo Cartão/Conta..." else conta_sel
                with c6:
                    orig_sel = st.selectbox("Fornecedor / Loja", obter_opcoes("Origem_Destino", LISTA_ORIG_BASE) + ["➕ Novo Fornecedor..."])
                    origem_destino = st.text_input("Nome do Fornecedor:") if orig_sel == "➕ Novo Fornecedor..." else orig_sel
                
                c7, c8 = st.columns(2)
                with c7: desc_resumo = st.text_input("Descrição Resumida (Ex: Uber, Aluguel)")
                with c8: resp_principal = st.selectbox("Responsável pelo Gasto", obter_opcoes("Responsavel", LISTA_RESP_BASE))
                
                st.markdown("##### 📅 Datas Fiscais (Mês da Compra vs Pagamento da Fatura)")
                md1, md2, md3, md4 = st.columns(4)
                meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
                with md1: ano_comp = st.selectbox("Ano da Compra", [2024, 2025, 2026, 2027], index=2)
                with md2: mes_comp = st.selectbox("Mês da Compra", meses_nomes, index=datetime.now().month - 1)
                with md3: ano_pag = st.selectbox("Ano de Pagamento (Fatura)", [2024, 2025, 2026, 2027], index=2)
                with md4: mes_pag = st.selectbox("Mês de Pagamento (Fatura)", meses_nomes, index=datetime.now().month - 1)
                
                st.markdown("---")
                cf1, cf2 = st.columns(2)
                with cf1: 
                    tipo_frequencia = st.radio("Como foi o pagamento?", ["À vista (Único)", "Parcelado"], horizontal=True)
                    parcelas = st.number_input("Quantidade de Parcelas", 2, 120, 2) if tipo_frequencia == "Parcelado" else 1
                with cf2: status_final = st.selectbox("A fatura/conta já foi paga?", ["Pendente", "Pago"])
                
                subcategoria = "Geral"
                ativo_ticker = ""

            # ----------------------------------------------------
            # FORMULÁRIO DE RECEITA (Otimizado)
            # ----------------------------------------------------
            elif tipo_mov == "Receita":
                c4, c5, c6 = st.columns(3)
                with c4: 
                    cat_sel = st.selectbox("Tipo de Receita", obter_opcoes("Categoria", LISTA_CAT_REC) + ["➕ Nova..."])
                    categoria = st.text_input("Nova Receita:") if cat_sel == "➕ Nova..." else cat_sel
                with c5:
                    if "Dividendos" in categoria or "JCP" in categoria or "Rendimentos" in categoria:
                        ativo_ticker = st.text_input("Ticker que pagou (Ex: MXRF11)").upper()
                        orig_sel = "Bolsa / B3"
                        origem_destino = orig_sel
                    else:
                        ativo_ticker = ""
                        orig_sel = st.selectbox("Quem pagou? (Origem)", obter_opcoes("Origem_Destino", ["Cliente", "Empregador", "Governo"]) + ["➕ Novo Pagador..."])
                        origem_destino = st.text_input("Novo Pagador:") if orig_sel == "➕ Novo Pagador..." else orig_sel
                with c6:
                    conta_sel = st.selectbox("Onde o dinheiro entrou?", ["Conta Corrente", "Pix", "Corretora", "Dinheiro Físico"])
                    conta_cartao = conta_sel
                    
                c7, c8 = st.columns(2)
                with c7: desc_resumo = st.text_input("Descrição (Ex: Salário, Venda Projeto X)")
                with c8: resp_principal = st.selectbox("Titular da Receita", obter_opcoes("Responsavel", LISTA_RESP_BASE))
                
                # Receita NÃO TEM frequência de parcelas nem fatura.
                status_final = st.radio("O dinheiro já está na conta?", ["Sim (Recebido/Pago)", "Ainda não (A Receber)"], horizontal=True)
                status_final = "Pago" if "Sim" in status_final else "Pendente"
                tipo_frequencia = "Único"
                parcelas = 1
                
                meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
                ano_comp = ano_pag = 2026 
                mes_comp = mes_pag = meses_nomes[datetime.now().month - 1]
                subcategoria = "Geral"

            # ----------------------------------------------------
            # FORMULÁRIO DE INVESTIMENTO (Gorila Style)
            # ----------------------------------------------------
            else: 
                st.info("💡 Investimento é construção de patrimônio. A ordem é executada e o dinheiro transferido.")
                c4, c5, c6 = st.columns(3)
                with c4: 
                    cat_sel = st.selectbox("Classe de Ativo", obter_opcoes("Categoria", LISTA_CAT_INV) + ["➕ Nova..."])
                    categoria = st.text_input("Nova Classe:") if cat_sel == "➕ Nova..." else cat_sel
                with c5:
                    ativo_ticker = st.text_input("Qual o Ticker/Ativo? (Ex: ITUB4, Tesouro Selic)").upper()
                    subcategoria = ativo_ticker
                with c6:
                    conta_cartao = st.selectbox("Dinheiro saiu de qual conta?", ["Conta Corrente", "Pix", "Poupança"])
                    
                c7, c8 = st.columns(2)
                with c7: 
                    orig_sel = st.selectbox("Para qual Corretora foi?", obter_opcoes("Origem_Destino", ["XP", "BTG", "NuInvest", "Rico", "Binance"]) + ["➕ Nova..."])
                    origem_destino = st.text_input("Nova Corretora:") if orig_sel == "➕ Nova..." else orig_sel
                with c8: 
                    desc_resumo = f"Aporte em {ativo_ticker}" if ativo_ticker else "Aporte de Investimento"
                    resp_principal = st.selectbox("Titular da Conta", obter_opcoes("Responsavel", LISTA_RESP_BASE))
                    
                # Investimento NÃO TEM pendência ou parcelas. 
                tipo_frequencia = "Único"
                parcelas = 1
                status_final = "Pago" 
                
                meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
                ano_comp = ano_pag = 2026
                mes_comp = mes_pag = meses_nomes[datetime.now().month - 1]

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Concluir Lançamento", type="primary", use_container_width=True):
            if valor_total > 0 and categoria and responsavel:
                if cat_sel == "➕ Nova..." and categoria: auto_salvar_cadastro("Categoria", categoria)
                if orig_sel == "➕ Novo..." and origem_destino: auto_salvar_cadastro("Origem_Destino", origem_destino)
                
                if ativo_ticker and tipo_mov == "Receita": desc_resumo = f"[{ativo_ticker}] {desc_resumo}"

                novas_linhas = []
                start_m_comp = int(mes_comp.split(" - ")[0])
                start_m_pag = int(mes_pag.split(" - ")[0])
                
                for i in range(parcelas):
                    comp_str = f"{int(ano_comp) + ((start_m_comp - 1 + i) // 12)}-{((start_m_comp - 1 + i) % 12) + 1:02d}"
                    pag_str = f"{int(ano_pag) + ((start_m_pag - 1 + i) // 12)}-{((start_m_pag - 1 + i) % 12) + 1:02d}"
                    val_parcela = valor_total / parcelas if tipo_frequencia == "Parcelado" else valor_total
                    desc_final = f"{desc_resumo} ({i+1}/{parcelas})" if tipo_frequencia == "Parcelado" else desc_resumo
                    
                    status_laco = status_final if i == 0 or status_final != "Pago" else "Pendente"
                    if tipo_mov in ["Investimento", "Receita"] and status_final == "Pago": status_laco = "Pago"
                    
                    novas_linhas.append({"user_email": st.session_state.user_email, "data_compra": str(data_ocorreu), "competencia": comp_str, "mes_pagamento": pag_str, "tipo": tipo_mov, "categoria": categoria, "subcategoria": subcategoria, "conta_cartao": conta_cartao, "valor": float(round(val_parcela, 2)), "descricao": desc_final, "parcela": f"{i+1}/{parcelas}" if tipo_frequencia == "Parcelado" else "Único", "responsavel": resp_principal, "origem_destino": origem_destino, "status": status_laco})

                try:
                    supabase.table("lancamentos").insert(novas_linhas).execute()
                    st.success("Operação Registrada!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Erro no banco de dados: {e}")
            else: st.warning("Preencha o Valor e a Categoria obrigatórios!")

    with aba_gerenciar:
        st.markdown("### ✏️ Edição de Histórico")
        if not df.empty:
            df_view = df[["ID", "Data", "Mes_Pagamento", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Descricao", "Valor", "Status"]].copy()
            st.data_editor(df_view, hide_index=True, use_container_width=True, disabled=["ID"])

# ========================================================
# 8. SUPER CENTRAL DE CADASTROS (RESTAURADA E VISÍVEL)
# ========================================================
with aba_cadastros:
    st.markdown("### ⚙️ Central de Cadastros e Configurações")
    st.write("Veja todas as opções salvas no seu histórico. Apagar daqui não afeta os gráficos.")
    
    col_dict = {"Categorias (Classes)": "Categoria", "Responsáveis": "Responsavel", "Fornecedores / Origens": "Origem_Destino"}
    tipo_cadastro = st.selectbox("Selecione a lista para gerenciar:", list(col_dict.keys()))
    col_db = col_dict[tipo_cadastro]
    
    # Busca 100% de tudo o que existe no banco para aquele usuário
    opcoes_atuais = obter_opcoes(col_db, LISTA_CAT_DESP + LISTA_CAT_REC + LISTA_CAT_INV if col_db=="Categoria" else (LISTA_RESP_BASE if col_db=="Responsavel" else LISTA_ORIG_BASE))
    
    c_cad1, c_cad2 = st.columns(2)
    with c_cad1:
        with st.container(border=True):
            st.markdown(f"#### ➕ Forçar Novo Cadastro")
            novo_item = st.text_input(f"Digitar novo(a) {tipo_cadastro}")
            if st.button("Salvar na Lista") and novo_item:
                auto_salvar_cadastro(col_db, novo_item)
                st.success("Salvo!")
                time.sleep(1)
                st.rerun()
                
    with c_cad2:
        with st.container(border=True):
            st.markdown(f"#### 🗑️ Ocultar do Formulário")
            if opcoes_atuais:
                item_apagar = st.selectbox("Selecione para colocar na Lista Negra:", opcoes_atuais)
                if st.button("Esconder Item"):
                    supabase.table("lancamentos").insert({"user_email": st.session_state.user_email, "data_compra": datetime.now().strftime("%Y-%m-%d"), "competencia": datetime.now().strftime("%Y-%m"), "mes_pagamento": datetime.now().strftime("%Y-%m"), "tipo": "Config_Excluida", "categoria": col_db, "subcategoria": item_apagar, "responsavel": st.session_state.user_nome, "origem_destino": "", "conta_cartao": "", "valor": 0.0, "descricao": "Oculto", "parcela": "-", "status": "Config"}).execute()
                    st.success("Item Ocultado!")
                    time.sleep(1)
                    st.rerun()
            else: st.write("Nenhum item encontrado.")

# ========================================================
# 9. ASSISTENTE IA
# ========================================================
with aba_assistente:
    st.markdown("### 🤖 Cérebro Digital")
    if modelo_ia and st.session_state.user_email:
        prompt = st.chat_input("Pergunte sobre seus dados...")
        if prompt:
            with st.chat_message("user"): st.markdown(prompt)
            try:
                hist_txt = df[["Data", "Tipo", "Categoria", "Valor"]].to_string() if not df.empty else "Vazio."
                resposta = modelo_ia.generate_content(f"Dados:\n{hist_txt}\nPergunta: {prompt}")
                with st.chat_message("assistant"): st.markdown(resposta.text)
            except Exception as e: st.error(f"Erro IA: {e}")
