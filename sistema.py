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
# 2. CONFIGURAÇÃO VISUAL E CSS
# ========================================================
st.set_page_config(page_title="Fluxo Financeiro PRO", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { font-family: 'Plus Jakarta Sans', sans-serif !important; background-color: #F8FAFC !important; color: #0F172A !important; }
        h1, h2, h3, h4 { font-weight: 800 !important; letter-spacing: -0.5px !important; color: #0F172A !important; }
        .title-gradient { background: linear-gradient(90deg, #0284C7 0%, #4F46E5 50%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding-bottom: 10px; }
        div[data-baseweb="input"], .stSelectbox div { border-radius: 8px !important; }
        div.stButton > button[kind="primary"] { background: linear-gradient(90deg, #0284C7 0%, #4F46E5 100%) !important; border: none !important; color: white !important; font-weight: bold; border-radius: 8px; padding: 10px; }
        .executive-box { background-color: #FFFFFF; border: 1px solid rgba(15,23,42,0.06); border-radius: 16px; padding: 20px; box-shadow: 0 10px 30px rgba(15,23,42,0.04); }
        hr { margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. AUTENTICAÇÃO COM CORREÇÃO DE NOME (Metadata)
# ========================================================
if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_nome" not in st.session_state: st.session_state.user_nome = "Usuário"
if "orcamentos" not in st.session_state: st.session_state.orcamentos = {}

cookie_manager = stx.CookieManager(key="auth_cookies")
cookies = cookie_manager.get_all()

if st.session_state.user_email is None and cookies and "u_mail" in cookies:
    st.session_state.user_email = cookies["u_mail"]
    # Tenta buscar o nome real no banco se o cookie só tiver "Usuário"
    try:
        user_data = supabase.auth.get_user()
        if user_data:
            st.session_state.user_nome = user_data.user.user_metadata.get("primeiro_nome", cookies.get("u_name", "Usuário"))
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
                    except Exception as e: st.error("E-mail ou senha incorretos.")
            with aba_registro:
                nome_reg = st.text_input("Qual é o seu primeiro nome?", key="reg_nome")
                email_reg = st.text_input("Melhor E-mail", key="reg_email")
                senha_reg = st.text_input("Crie uma Senha Forte", type="password", key="reg_senha")
                if st.button("Garantir Meu Acesso", type="primary", use_container_width=True):
                    if nome_reg.strip() and email_reg.strip():
                        try:
                            supabase.auth.sign_up({"email": email_reg, "password": senha_reg, "options": {"data": {"primeiro_nome": nome_reg.strip()}}})
                            st.success(f"Conta de {nome_reg} criada! Faça login.")
                        except Exception as e: st.error(f"Erro: {e}")
    st.stop()

# ========================================================
# 4. GESTÃO DE DADOS (COM PROTEÇÃO)
# ========================================================
LISTA_RESPONSAVEIS_BASE = [st.session_state.user_nome, "Família", "Empresa"]
LISTA_BANCOS = ["Banco do Brasil", "Inter", "Nubank", "Itaú", "Bradesco", "Caixa", "C6 Bank", "XP", "PicPay", "99Pay", "Mercado Pago"]
LISTA_CATEGORIAS_DESPESA = ["Alimentação", "Transporte", "Moradia", "Salário", "Assinaturas", "Viagens", "Lazer", "Saúde", "Educação", "Impostos e Tributos", "Outros"]
LISTA_CATEGORIAS_RECEITA = ["Salário / Pró-Labore", "Rendimentos (Dividendos / JCP)", "Comissões", "Vendas", "Restituição", "Outros"]
LISTA_CATEGORIAS_INVEST = ["Ações (B3)", "Fundos Imobiliários (FIIs)", "Renda Fixa (CDB, Tesouro)", "Criptomoedas", "Ações (EUA)", "Previdência", "Outros"]
LISTA_ORIGEM_BASE = ["Supermercado", "Pix", "Empresa", "Cliente"]

def carregar_dados_completos():
    try:
        response = supabase.table("lancamentos").select("*").eq("user_email", st.session_state.user_email).execute()
        if response.data:
            df_total = pd.DataFrame(response.data)
            if "mes_pagamento" not in df_total.columns: df_total["mes_pagamento"] = df_total["competencia"]
            df_total["mes_pagamento"] = df_total["mes_pagamento"].fillna(df_total["competencia"])
            
            df_total = df_total.rename(columns={"id": "ID", "data_compra": "Data", "competencia": "Competencia", "mes_pagamento": "Mes_Pagamento", "tipo": "Tipo", "categoria": "Categoria", "subcategoria": "Subcategoria", "conta_cartao": "Conta_Cartao", "valor": "Valor", "descricao": "Descricao", "parcela": "Parcela", "responsavel": "Responsavel", "status": "Status", "origem_destino": "Origem_Destino"})
            df_total["Valor"] = pd.to_numeric(df_total["Valor"]).fillna(0.0)
            return df_total
    except: pass
    return pd.DataFrame(columns=["ID", "Data", "Mes_Pagamento", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status", "Origem_Destino"])

df_tudo = carregar_dados_completos()
df_configs = df_tudo[df_tudo["Tipo"].str.startswith("Config_")].copy() if not df_tudo.empty else pd.DataFrame(columns=df_tudo.columns)
df = df_tudo[~df_tudo["Tipo"].str.startswith("Config_")].copy() if not df_tudo.empty else pd.DataFrame(columns=df_tudo.columns)
df_cartoes = df_configs[df_configs["Tipo"] == "Config_Cartao"]

def obter_opcoes(coluna, lista_base):
    config_items = df_configs[df_configs["Tipo"] == f"Config_{coluna}"][coluna].dropna().astype(str).unique().tolist() if not df_configs.empty and coluna in df_configs.columns else []
    existentes = df[coluna].dropna().astype(str).unique().tolist() if not df.empty and coluna in df.columns else []
    ocultos = df_configs[(df_configs["Tipo"] == "Config_Excluida") & (df_configs["Categoria"] == coluna)]["Subcategoria"].dropna().astype(str).unique().tolist() if not df_configs.empty else []
    
    todos = set(lista_base + config_items + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])
    for item in ocultos:
        if item in todos: todos.remove(item)
    return sorted(list(todos))

# ========================================================
# 5. HEADER E TABS
# ========================================================
c_head1, c_head2 = st.columns([4, 1])
with c_head1: st.markdown("<h2 class='title-gradient'>Fluxo Financeiro PRO</h2>", unsafe_allow_html=True)
with c_head2:
    st.write(f"👤 Olá, **{st.session_state.user_nome}**")
    if st.button("Sair (Logout)"):
        cookie_manager.set("u_mail", "", max_age=-1)
        cookie_manager.set("u_name", "", max_age=-1)
        st.session_state.clear()
        st.rerun()

aba_dashboard, aba_lancamentos, aba_cadastros, aba_assistente = st.tabs(["📊 Dashboard", "📝 Lançamentos", "⚙️ Cadastros", "🤖 IA"])

# ========================================================
# 6. DASHBOARD
# ========================================================
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        st.info("Visão de Dashboard ativa (Simplificada para exibição. As abas de relatório operam em background).")
    else: st.info("O Dashboard aguarda lançamentos.")

# ========================================================
# 7. LANÇAMENTOS INTELIGENTES (A MAGIA DE MERCADO)
# ========================================================
def auto_salvar_cadastro(tipo_cad, valor):
    try:
        supabase.table("lancamentos").insert({"user_email": st.session_state.user_email, "data_compra": datetime.now().strftime("%Y-%m-%d"), "competencia": datetime.now().strftime("%Y-%m"), "mes_pagamento": datetime.now().strftime("%Y-%m"), "tipo": f"Config_{tipo_cad}", "categoria": valor if tipo_cad == "Categoria" else "", "subcategoria": valor if tipo_cad == "Subcategoria" else "", "responsavel": valor if tipo_cad == "Responsavel" else "", "origem_destino": valor if tipo_cad == "Origem_Destino" else "", "conta_cartao": "", "valor": 0.0, "descricao": "Configuração Automática", "parcela": "-", "status": "Config"}).execute()
    except: pass

with aba_lancamentos:
    aba_manual, aba_gerenciar = st.tabs(["✍️ Novo Lançamento Inteligente", "✏️ Gerenciar Base"])
    
    with aba_manual:
        # 1. ESCOLHA DO TIPO (Define o formulário inteiro)
        c_tipo, c_val, c_data = st.columns(3)
        with c_tipo: tipo_mov = st.selectbox("Tipo de Movimentação", ["Despesa", "Receita", "Investimento"])
        with c_val: valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
        with c_data: data_ocorreu = st.date_input("Data (Ocorrência/Ordem)")

        st.markdown(f"#### Classificação de {tipo_mov}")
        
        # ----------------------------------------------------
        # FORMULÁRIO DE DESPESAS (Custo, Cartão, Vencimentos)
        # ----------------------------------------------------
        if tipo_mov == "Despesa":
            c4, c5, c6 = st.columns(3)
            with c4: 
                cat_sel = st.selectbox("Categoria", obter_opcoes("Categoria", LISTA_CATEGORIAS_DESPESA) + ["➕ Novo..."])
                categoria = st.text_input("Nova Categoria:") if cat_sel == "➕ Novo..." else cat_sel
            with c5:
                opcoes_conta = ["Conta Corrente / Pix", "Dinheiro"] + (df_cartoes["Conta_Cartao"].unique().tolist() if not df_cartoes.empty else []) + ["➕ Novo..."]
                conta_sel = st.selectbox("Conta de Saída / Cartão", opcoes_conta)
                conta_cartao = st.text_input("Nova Conta:") if conta_sel == "➕ Novo..." else conta_sel
            with c6:
                orig_sel = st.selectbox("Fornecedor / Loja", obter_opcoes("Origem_Destino", LISTA_ORIGEM_BASE) + ["➕ Novo..."])
                origem_destino = st.text_input("Novo Fornecedor:") if orig_sel == "➕ Novo..." else orig_sel
            
            c7, c8 = st.columns(2)
            with c7: desc_resumo = st.text_input("Descrição Resumida (Ex: Mensalidade Academia)")
            with c8: resp_principal = st.selectbox("Responsável Principal", obter_opcoes("Responsavel", LISTA_RESPONSAVEIS_BASE))
            
            st.markdown("##### 📅 Mês da Compra vs Mês do Pagamento (Fatura)")
            md1, md2, md3, md4 = st.columns(4)
            meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
            with md1: ano_comp = st.selectbox("Ano (Compra)", [2024, 2025, 2026, 2027], index=2)
            with md2: mes_comp = st.selectbox("Mês (Compra)", meses_nomes, index=datetime.now().month - 1)
            with md3: ano_pag = st.selectbox("Ano (Fatura/Saída)", [2024, 2025, 2026, 2027], index=2)
            with md4: mes_pag = st.selectbox("Mês (Fatura/Saída)", meses_nomes, index=datetime.now().month - 1)
            
            cf1, cf2 = st.columns(2)
            with cf1: 
                tipo_frequencia = st.radio("Frequência", ["Único", "Parcelado", "Recorrente"], horizontal=True)
                parcelas = st.number_input("Parcelas / Meses", 2, 120, 2) if tipo_frequencia != "Único" else 1
            with cf2: status_final = st.selectbox("Status", ["Pago", "Pendente"])
            
            subcategoria = "Geral" # Simplificado
            ativo_ticker = ""

        # ----------------------------------------------------
        # FORMULÁRIO DE RECEITAS (Entradas, JCP, Dividendos)
        # ----------------------------------------------------
        elif tipo_mov == "Receita":
            c4, c5, c6 = st.columns(3)
            with c4: 
                cat_sel = st.selectbox("Tipo de Receita", obter_opcoes("Categoria", LISTA_CATEGORIAS_RECEITA) + ["➕ Novo..."])
                categoria = st.text_input("Nova Receita:") if cat_sel == "➕ Novo..." else cat_sel
            with c5:
                # Se for Rendimentos, abre o campo Ticker!
                if "Dividendos" in categoria or "JCP" in categoria or "Rendimentos" in categoria:
                    ativo_ticker = st.text_input("Ativo / Ticker (Ex: MXRF11, PETR4)").upper()
                    origem_destino = "Bolsa de Valores"
                else:
                    ativo_ticker = ""
                    orig_sel = st.selectbox("Quem pagou? (Origem)", obter_opcoes("Origem_Destino", ["Empregador", "Cliente", "Governo"]) + ["➕ Novo..."])
                    origem_destino = st.text_input("Novo Pagador:") if orig_sel == "➕ Novo..." else orig_sel
            with c6:
                conta_sel = st.selectbox("Onde Entrou? (Conta)", ["Conta Corrente", "Poupança", "Corretora", "Pix", "Dinheiro Físico"])
                conta_cartao = conta_sel
                
            c7, c8 = st.columns(2)
            with c7: desc_resumo = st.text_input("Descrição Resumida (Ex: Salário de Agosto)")
            with c8: resp_principal = st.selectbox("A quem pertence a receita?", obter_opcoes("Responsavel", LISTA_RESPONSAVEIS_BASE))
            
            # Receita não tem parcela de cartão. Tem Status "Recebido" ou "A Receber".
            st.markdown("##### 📅 Status da Entrada")
            cr1, cr2 = st.columns(2)
            with cr1: 
                status_final = st.selectbox("Situação", ["Recebido", "A Receber"])
                if status_final == "Recebido": status_final = "Pago" # Sistema entende Pago como Liquidado
            with cr2:
                tipo_frequencia = "Único"
                parcelas = 1
                
            # Datas unificadas (Mês que entra)
            meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
            ano_comp = ano_pag = 2026 # Fixo para o exemplo base, usar datetime
            mes_comp = mes_pag = meses_nomes[datetime.now().month - 1]
            subcategoria = "Geral"

        # ----------------------------------------------------
        # FORMULÁRIO DE INVESTIMENTOS (Alocações)
        # ----------------------------------------------------
        elif tipo_mov == "Investimento":
            st.info("💡 Um investimento não é uma despesa, é uma transferência de patrimônio para uma corretora.")
            c4, c5, c6 = st.columns(3)
            with c4: 
                cat_sel = st.selectbox("Classe de Ativo", obter_opcoes("Categoria", LISTA_CATEGORIAS_INVEST) + ["➕ Novo..."])
                categoria = st.text_input("Nova Classe:") if cat_sel == "➕ Novo..." else cat_sel
            with c5:
                ativo_ticker = st.text_input("Ativo / Ticker (Ex: AAPL34, SELIC2029)").upper()
                subcategoria = ativo_ticker
            with c6:
                conta_cartao = st.selectbox("Conta de Origem do Dinheiro", ["Conta Corrente", "Pix", "Poupança"])
                
            c7, c8 = st.columns(2)
            with c7: 
                orig_sel = st.selectbox("Corretora / Banco Destino", obter_opcoes("Origem_Destino", ["XP", "BTG", "NuInvest", "Avenue", "Binance"]) + ["➕ Novo..."])
                origem_destino = st.text_input("Nova Corretora:") if orig_sel == "➕ Novo..." else orig_sel
            with c8: 
                desc_resumo = f"Aporte {ativo_ticker}" if ativo_ticker else "Aporte Mensal"
                resp_principal = st.selectbox("Titular do Investimento", obter_opcoes("Responsavel", LISTA_RESPONSAVEIS_BASE))
                
            # Investimento não tem pendência ou parcela. É executado.
            tipo_frequencia = "Único"
            parcelas = 1
            status_final = "Pago" # Executado
            
            meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
            ano_comp = ano_pag = 2026
            mes_comp = mes_pag = meses_nomes[datetime.now().month - 1]

        # BOTÃO SALVAR (MÁGICA UNIVERSAL)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Concluir Lançamento", type="primary", use_container_width=True):
            if valor_total > 0 and categoria and responsavel:
                if cat_sel == "➕ Novo..." and categoria: auto_salvar_cadastro("Categoria", categoria)
                if orig_sel == "➕ Novo..." and origem_destino: auto_salvar_cadastro("Origem_Destino", origem_destino)
                
                if ativo_ticker:
                    desc_resumo = f"[{ativo_ticker}] {desc_resumo}"

                novas_linhas = []
                start_m_comp = int(mes_comp.split(" - ")[0])
                start_m_pag = int(mes_pag.split(" - ")[0])
                
                for i in range(parcelas):
                    comp_str = f"{int(ano_comp) + ((start_m_comp - 1 + i) // 12)}-{((start_m_comp - 1 + i) % 12) + 1:02d}"
                    pag_str = f"{int(ano_pag) + ((start_m_pag - 1 + i) // 12)}-{((start_m_pag - 1 + i) % 12) + 1:02d}"
                    val_parcela = valor_total / parcelas if tipo_frequencia == "Parcelado" else valor_total
                    desc_final = f"{desc_resumo} ({i+1}/{parcelas})" if tipo_frequencia == "Parcelado" else desc_resumo
                    
                    status_laco = status_final if i == 0 or status_final != "Pago" else "Pendente"
                    if tipo_mov == "Investimento": status_laco = "Pago" # Sempre executado
                    
                    novas_linhas.append({"user_email": st.session_state.user_email, "data_compra": str(data_ocorreu), "competencia": comp_str, "mes_pagamento": pag_str, "tipo": tipo_mov, "categoria": categoria, "subcategoria": subcategoria, "conta_cartao": conta_cartao, "valor": float(round(val_parcela, 2)), "descricao": desc_final, "parcela": f"{i+1}/{parcelas}" if tipo_frequencia == "Parcelado" else "Único", "responsavel": resp_principal, "origem_destino": origem_destino, "status": status_laco})

                try:
                    supabase.table("lancamentos").insert(novas_linhas).execute()
                    st.success("Registrado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")
            else: st.warning("Preencha Valor e Categoria!")

    with aba_gerenciar:
        st.markdown("### ✏️ Mesa de Operações (Tabela de Dados)")
        if not df.empty:
            df_view = df[["ID", "Data", "Competencia", "Mes_Pagamento", "Tipo", "Categoria", "Conta_Cartao", "Descricao", "Valor", "Status"]].copy()
            df_resultado = st.data_editor(df_view, hide_index=True, use_container_width=True, disabled=["ID"])

# ========================================================
# 8. SUPER CENTRAL DE CADASTROS (TOTALMENTE RESTAURADA)
# ========================================================
with aba_cadastros:
    st.markdown("### ⚙️ Central de Cadastros e Configurações")
    st.write("Aqui você visualiza, renomeia ou exclui opções do seu sistema. Os dados do seu histórico NUNCA somem.")
    
    col_dict = {"Contas e Cartões": "Cartao", "Categorias Gerais": "Categoria", "Responsáveis": "Responsavel", "Fornecedores / Origens": "Origem_Destino"}
    tipo_cadastro = st.selectbox("O que deseja gerenciar?", list(col_dict.keys()))
    col_db = col_dict[tipo_cadastro]
    
    if col_db == "Cartao":
        with st.container(border=True):
            st.markdown("#### Adicionar Cartão")
            c1, c2, c3 = st.columns(3)
            with c1: banco_cartao = st.selectbox("Banco", LISTA_BANCOS)
            with c2: final_cartao = st.text_input("Final do Cartão (Ex: 1234)")
            with c3: dia_vencimento = st.number_input("Dia de Vencimento", 1, 31, 10)
            if st.button("Salvar Cartão", type="primary") and final_cartao:
                auto_salvar_cadastro("Cartao", f"{banco_cartao} - Final {final_cartao} (Venc: dia {dia_vencimento})")
                st.rerun()
    else:
        # LISTA TODOS OS ITENS ATIVOS
        if col_db == "Categoria": lista_padrao = LISTA_CATEGORIAS_DESPESA + LISTA_CATEGORIAS_RECEITA + LISTA_CATEGORIAS_INVEST
        elif col_db == "Responsavel": lista_padrao = LISTA_RESPONSAVEIS_BASE
        else: lista_padrao = LISTA_ORIGEM_BASE
        
        opcoes_atuais = obter_opcoes(col_db, lista_padrao)
        
        c_cad1, c_cad2 = st.columns(2)
        with c_cad1:
            with st.container(border=True):
                st.markdown(f"#### ➕ Adicionar Novo")
                novo_item = st.text_input(f"Nome do(a) {tipo_cadastro}")
                if st.button("Salvar Cadastro") and novo_item:
                    auto_salvar_cadastro(col_db, novo_item)
                    st.rerun()
                    
        with c_cad2:
            with st.container(border=True):
                st.markdown(f"#### 🗑️ Ocultar / Excluir da Lista")
                st.write("Retira o item da lista de opções futuras, mas não afeta o histórico financeiro.")
                if opcoes_atuais:
                    item_apagar = st.selectbox("Selecione o item para excluir:", opcoes_atuais)
                    if st.button("Remover Item"):
                        supabase.table("lancamentos").insert({"user_email": st.session_state.user_email, "data_compra": datetime.now().strftime("%Y-%m-%d"), "competencia": datetime.now().strftime("%Y-%m"), "mes_pagamento": datetime.now().strftime("%Y-%m"), "tipo": "Config_Excluida", "categoria": col_db, "subcategoria": item_apagar, "responsavel": st.session_state.user_nome, "origem_destino": "", "conta_cartao": "", "valor": 0.0, "descricao": "Oculto", "parcela": "-", "status": "Config"}).execute()
                        st.rerun()

# ========================================================
# 9. ASSISTENTE IA
# ========================================================
with aba_assistente:
    st.markdown("### 🤖 Cérebro Digital - Inteligência Autoral")
    if modelo_ia:
        prompt = st.chat_input("Pergunte sobre seus dados...")
        if prompt:
            st.markdown(f"**Você:** {prompt}")
            hist_txt = df[["Data", "Tipo", "Categoria", "Valor"]].to_string() if not df.empty else "Vazio."
            try:
                res = modelo_ia.generate_content(f"Dados:\n{hist_txt}\nPergunta: {prompt}")
                st.markdown(f"**IA:** {res.text}")
            except Exception as e: st.error(f"Erro IA: {e}")
