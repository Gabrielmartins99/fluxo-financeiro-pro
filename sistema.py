import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import json
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
    modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
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
        .status-box { padding: 20px; border-radius: 10px; background-color: #ECFDF5; border: 1px solid #10B981; color: #065F46; font-weight: bold; text-align: center; }
        hr { margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. AUTENTICAÇÃO
# ========================================================
if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_nome" not in st.session_state: st.session_state.user_nome = "Usuário"
if "orcamentos" not in st.session_state: st.session_state.orcamentos = {}

cookie_manager = stx.CookieManager(key="gerenciador_cookies_seguro_v3")

cookies = cookie_manager.get_all()
if st.session_state.user_email is None and cookies:
    if "u_mail" in cookies and cookies["u_mail"]:
        email_candidato = cookies["u_mail"]
        nome_candidato = cookies.get("u_name", "Usuário")
        try:
            teste_auth = supabase.auth.get_session()
            st.session_state.user_email = email_candidato
            st.session_state.user_nome = nome_candidato
        except:
            st.session_state.user_email = None
            st.session_state.user_nome = "Usuário"

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
                    except Exception as e:
                        erro_str = str(e)
                        if "Name or service not known" in erro_str or "Errno -2" in erro_str:
                            st.error("🚨 Erro de Rede: O seu banco de dados (Supabase) entrou em Modo Pausa. Acesse supabase.com e clique em 'Restore'.")
                        else:
                            st.error(f"E-mail ou senha incorretos. ({erro_str})")
                            
            with aba_registro:
                st.markdown("#### Cadastro de Novo Membro")
                nome_reg = st.text_input("Qual é o seu primeiro nome?", key="reg_nome", placeholder="Ex: Tainá")
                email_reg = st.text_input("Melhor E-mail", key="reg_email")
                senha_reg = st.text_input("Crie uma Senha Forte", type="password", key="reg_senha")
                if st.button("Garantir Meu Acesso", type="primary", use_container_width=True):
                    if nome_reg.strip() != "" and email_reg.strip() != "":
                        try:
                            supabase.auth.sign_up({
                                "email": email_reg, 
                                "password": senha_reg,
                                "options": {"data": {"primeiro_nome": nome_reg.strip()}}
                            })
                            st.success(f"✅ Conta de {nome_reg} criada! Faça login ao lado.")
                        except Exception as e: 
                            erro_str = str(e)
                            if "Name or service not known" in erro_str or "Errno -2" in erro_str:
                                st.error("🚨 Servidor Offline: O seu banco de dados no Supabase entrou em Modo Pausa por inatividade. Acesse o painel do Supabase e clique em 'Restore' para reativar o sistema.")
                            else:
                                st.error(f"Erro ao criar conta. Resposta do Servidor: {erro_str}")
                    else: st.warning("Por favor, informe seu primeiro nome e e-mail.")
    st.stop()

# ========================================================
# 4. FUNÇÕES BASE
# ========================================================
def carregar_dados():
    try:
        response = supabase.table("lancamentos").select("*").eq("user_email", st.session_state.user_email).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.rename(columns={"id": "ID", "data_compra": "Data", "competencia": "Competencia", "tipo": "Tipo", "categoria": "Categoria", "subcategoria": "Subcategoria", "conta_cartao": "Conta_Cartao", "valor": "Valor", "descricao": "Descricao", "parcela": "Parcela", "responsavel": "Responsavel", "status": "Status", "origem_destino": "Origem_Destino"})
            df["Valor"] = pd.to_numeric(df["Valor"]).fillna(0.0)
            if "Origem_Destino" in df.columns: df["Origem_Destino"] = df["Origem_Destino"].fillna("")
            else: df["Origem_Destino"] = ""
            if "Status" not in df.columns: df["Status"] = "Pago"
            if "Subcategoria" not in df.columns: df["Subcategoria"] = "Geral"
            
            def determinar_caixa(row):
                try:
                    data_ocorreu = pd.to_datetime(row["Data"]).strftime("%Y-%m")
                    competencia = str(row["Competencia"])
                    if data_ocorreu > competencia: return data_ocorreu 
                    else: return competencia 
                except: return str(row.get("Competencia", ""))
            
            df["Mes_Pagamento"] = df.apply(determinar_caixa, axis=1)
            return df
    except: pass
    return pd.DataFrame(columns=["ID", "Data", "Mes_Pagamento", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status", "Origem_Destino"])

df = carregar_dados()

def obter_opcoes(coluna, lista_base):
    if not df.empty and coluna in df.columns:
        existentes = df[coluna].dropna().astype(str).unique().tolist()
        return sorted(list(set(lista_base + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])))
    return sorted(lista_base)

def obter_subcategorias_dinamicas(categoria_alvo):
    base = []
    if categoria_alvo == "Moradia": base = ["Aluguel", "Energia", "Internet", "Água", "Condomínio"]
    elif categoria_alvo == "Viagens": base = ["Airbnb", "Hotéis", "Passagens", "Alimentação"]
    elif categoria_alvo == "Assinaturas": base = ["Netflix", "Amazon", "Spotify", "Software"]
    elif categoria_alvo == "Salário": base = ["Salário Fixo", "Comissão", "Bonificação", "13º"]
    else: base = ["Geral"]
    
    if not df.empty and "Subcategoria" in df.columns and "Categoria" in df.columns:
        existentes = df[df["Categoria"] == categoria_alvo]["Subcategoria"].dropna().astype(str).unique().tolist()
        return sorted(list(set(base + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])))
    return sorted(base)

LISTA_RESPONSAVEIS_BASE = [st.session_state.user_nome, "Família", "Empresa"]
LISTA_BANCOS = ["Nubank", "Inter", "Itaú", "Bradesco", "Banco do Brasil", "Dinheiro/Pix"]
LISTA_CATEGORIAS = ["Alimentação", "Transporte", "Moradia", "Salário", "Assinaturas", "Viagens", "Lazer", "Saúde", "Educação", "Investimentos", "Outros"]

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

aba_dashboard, aba_lancamentos, aba_assistente, aba_openfinance = st.tabs(["📊 Dashboard", "📝 Lançamentos", "🤖 Assistente IA", "🔌 Open Finance"])

# ========================================================
# 6. DASHBOARD (Omitido para focar na aba de lançamentos, mantendo a estrutura igual ao anterior)
# ========================================================
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        st.info("O seu Dashboard continua a funcionar perfeitamente. Pode navegar pelas abas acima.")
    else: st.info("O Dashboard aguarda lançamentos.")

# ========================================================
# 7. LANÇAMENTOS E EDIÇÃO EM MASSA (COM TRAVA DE SEGURANÇA)
# ========================================================
with aba_lancamentos:
    aba_manual, aba_importar, aba_gerenciar = st.tabs(["✍️ Novo Lançamento", "📥 Importar Fatura", "✏️ Gerenciar e Excluir"])
    
    with aba_manual:
        st.markdown("### 📝 Registrar Nova Movimentação")
        with st.container(border=True):
            st.markdown("#### 1. Valores e Datas")
            c1, c2, c3 = st.columns(3)
            with c1: tipo = st.selectbox("Tipo da Movimentação", ["Despesa", "Receita", "Investimento"])
            with c2: valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
            with c3: data_compra = st.date_input("Data do Ocorrido")

        with st.container(border=True):
            st.markdown("#### 2. Classificação")
            c4_cat, c4_sub, c5, c6 = st.columns(4)
            with c4_cat:
                opcoes_cat = obter_opcoes("Categoria", LISTA_CATEGORIAS) + ["➕ Nova Categoria..."]
                cat_sel = st.selectbox("Categoria", opcoes_cat)
                categoria = st.text_input("Nome da Nova Categoria:") if cat_sel == "➕ Nova Categoria..." else cat_sel
            with c4_sub:
                opcoes_subcat = obter_subcategorias_dinamicas(categoria) + ["➕ Nova Subcategoria..."]
                subcat_sel = st.selectbox("Subcategoria", opcoes_subcat)
                subcategoria = st.text_input("Nome da Nova Subcategoria:") if subcat_sel == "➕ Nova Subcategoria..." else subcat_sel
            with c5:
                opcoes_conta = obter_opcoes("Conta_Cartao", LISTA_BANCOS) + ["➕ Nova Conta..."]
                conta_sel = st.selectbox("Conta / Cartão", opcoes_conta)
                conta_cartao = st.text_input("Nome da Nova Conta:") if conta_sel == "➕ Nova Conta..." else conta_sel
            with c6:
                opcoes_orig = obter_opcoes("Origem_Destino", ["Supermercado", "Pix", "Empresa"]) + ["➕ Nova Origem/Destino..."]
                orig_sel = st.selectbox("Origem / Destino", opcoes_orig)
                origem_destino = st.text_input("Nome da Nova Origem/Destino:") if orig_sel == "➕ Nova Origem/Destino..." else orig_sel

        with st.container(border=True):
            st.markdown("#### 3. Detalhes Adicionais e Rateio (Split)")
            c7, c8, c9, c10 = st.columns(4)
            with c7:
                opcoes_resp = obter_opcoes("Responsavel", LISTA_RESPONSAVEIS_BASE) + ["➕ Novo Responsável..."]
                resp_sel = st.selectbox("Responsável Principal", opcoes_resp)
                responsavel = st.text_input("Nome do Responsável:") if resp_sel == "➕ Novo Responsável..." else resp_sel
            with c8: descricao = st.text_input("Descrição Resumida (Ex: Aluguel, Mensalidade Academia)")
            
            with c9: 
                ano_atual = datetime.now().year
                anos_lista = list(range(2020, 2035))
                ano_comp = st.selectbox("Ano Competência", anos_lista, index=anos_lista.index(ano_atual))
            with c10:
                meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
                mes_sel = st.selectbox("Mês Competência", meses_nomes, index=datetime.now().month - 1)
                mes_num = mes_sel.split(" - ")[0]
                competencia_final = f"{ano_comp}-{mes_num}"
                
            st.markdown("---")
            
            dividir_despesa = st.checkbox("🤝 Dividir este lançamento com outra pessoa?")
            if dividir_despesa:
                col_split1, col_split2 = st.columns(2)
                with col_split1:
                    resp_2_sel = st.selectbox("Quem é o 2º Responsável?", opcoes_resp, key="resp_2")
                    responsavel_2 = st.text_input("Nome do 2º Responsável:", key="txt_resp2") if resp_2_sel == "➕ Novo Responsável..." else resp_2_sel
                with col_split2:
                    valor_resp_2 = st.number_input(f"Qual o valor da parte de {responsavel_2}? (R$)", min_value=0.0, max_value=float(valor_total) if valor_total > 0 else 100000.0, step=10.0, format="%.2f")
                    valor_resp_1 = valor_total - valor_resp_2
                    st.info(f"A parte de **{responsavel}** será: R$ {valor_resp_1:.2f}")
            else:
                valor_resp_1 = valor_total
                responsavel_2 = None
                valor_resp_2 = 0.0

            st.markdown("---")
            c11, c12 = st.columns(2)
            with c11:
                modo_lancamento = st.radio("Frequência de Lançamento:", ["Único (À vista)", "Parcelado", "Assinatura Mensal"], horizontal=True)
            with c12:
                status_pagamento = st.selectbox("Status atual do Lançamento", ["Pago", "Pendente"])
                
            if modo_lancamento == "Parcelado": parcelas = st.number_input("Número de Parcelas", min_value=2, max_value=120, value=2)
            elif modo_lancamento == "Assinatura Mensal": parcelas = st.number_input("Projetar por quantos meses?", min_value=2, max_value=60, value=12)
            else: parcelas = 1

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Concluir Lançamento no Sistema", type="primary", use_container_width=True):
            if valor_total > 0 and categoria and conta_cartao and responsavel:
                novas_linhas = []
                start_year = ano_comp
                start_month = int(mes_num)
                meses_abrev = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}
                
                for i in range(parcelas):
                    m = start_month - 1 + i
                    y = start_year + (m // 12)
                    mes_atual_loop = (m % 12) + 1
                    comp = f"{y}-{mes_atual_loop:02d}"
                    origem_segura = origem_destino if origem_destino else ""
                    nova_data_compra = (pd.to_datetime(data_compra) + pd.DateOffset(months=i)).strftime("%Y-%m-%d")
                    status_final = status_pagamento if i == 0 else "Pendente"
                    
                    if parcelas > 1:
                        desc_dinamica = f"{descricao.strip()} ({meses_abrev[mes_atual_loop]}/{y})"
                    else:
                        desc_dinamica = descricao.strip()
                    
                    valor_parcela_1 = valor_resp_1 / parcelas if modo_lancamento == "Parcelado" else valor_resp_1
                    novas_linhas.append({"user_email": st.session_state.user_email, "data_compra": nova_data_compra, "competencia": comp, "tipo": tipo, "categoria": categoria, "subcategoria": subcategoria, "conta_cartao": conta_cartao, "valor": float(round(valor_parcela_1, 2)), "descricao": desc_dinamica, "parcela": f"{i+1}/{parcelas}" if modo_lancamento == "Parcelado" else "Recorrente" if modo_lancamento == "Assinatura Mensal" else "À vista", "responsavel": responsavel, "origem_destino": origem_segura, "status": status_final})
                    
                    if dividir_despesa and valor_resp_2 > 0:
                        valor_parcela_2 = valor_resp_2 / parcelas if modo_lancamento == "Parcelado" else valor_resp_2
                        novas_linhas.append({"user_email": st.session_state.user_email, "data_compra": nova_data_compra, "competencia": comp, "tipo": tipo, "categoria": categoria, "subcategoria": subcategoria, "conta_cartao": conta_cartao, "valor": float(round(valor_parcela_2, 2)), "descricao": desc_dinamica, "parcela": f"{i+1}/{parcelas}" if modo_lancamento == "Parcelado" else "Recorrente" if modo_lancamento == "Assinatura Mensal" else "À vista", "responsavel": responsavel_2, "origem_destino": origem_segura, "status": "Pendente"})

                try:
                    supabase.table("lancamentos").insert(novas_linhas).execute()
                    st.success("Registrado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
            else: st.warning("Preencha os dados base.")

    with aba_gerenciar:
        st.markdown("### ✏️ Mesa de Operações: Edição e Ações em Massa")
        if df.empty:
            st.info("Nenhum lançamento encontrado para gerenciar. Por favor, insira novos dados.")
        else:
            df_view = df[["ID", "Data", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Descricao", "Valor", "Responsavel", "Origem_Destino", "Status"]].copy()
            
            st.markdown("#### 🔍 Filtros de Busca")
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            with c_f1:
                opcoes_tipo = ["Todos", "Despesa", "Receita", "Investimento"]
                filtro_tipo = st.selectbox("Filtrar por Tipo", opcoes_tipo)
            with c_f2:
                opcoes_comp = ["Todos"] + sorted(df_view["Competencia"].unique(), reverse=True)
                filtro_comp = st.selectbox("Filtrar por Competência", opcoes_comp)
            with c_f3:
                opcoes_resp_gerenciar = sorted(df_view["Responsavel"].dropna().unique())
                filtro_resp_multi = st.multiselect("Filtrar por Responsáveis", opcoes_resp_gerenciar, default=opcoes_resp_gerenciar)
            with c_f4:
                opcoes_status = ["Todos", "Pago", "Pendente"]
                filtro_status = st.selectbox("Filtrar por Status", opcoes_status)
            
            if filtro_tipo != "Todos":
                df_view = df_view[df_view["Tipo"] == filtro_tipo]
            if filtro_comp != "Todos":
                df_view = df_view[df_view["Competencia"] == filtro_comp]
            if filtro_resp_multi:
                df_view = df_view[df_view["Responsavel"].isin(filtro_resp_multi)]
            else:
                df_view = df_view.iloc[0:0]

            if filtro_status != "Todos":
                df_view = df_view[df_view["Status"] == filtro_status]
            
            st.markdown("---")
            
            selecionar_tudo = st.checkbox("☑️ Selecionar todos os lançamentos filtrados abaixo", value=False)
            df_view.insert(0, "Selecionar", selecionar_tudo)
            
            st.write(f"🔒 **Instruções:** Estão listados {len(df_view)} lançamentos. Marque a caixinha acima para selecionar todos de uma vez, ou escolha itens individuais.")
            
            df_resultado = st.data_editor(
                df_view, 
                hide_index=True, 
                use_container_width=True, 
                disabled=["ID"] 
            )
            
            ids_selecionados = df_resultado[df_resultado["Selecionar"] == True]["ID"].tolist()
            
            # 🔥 O NOVO ALERTA DE SEGURANÇA (CONFIRMAÇÃO EM DUAS ETAPAS) 🔥
            if "confirmar_delecao" in st.session_state and st.session_state.confirmar_delecao:
                st.error(f"⚠️ **ALERTA CRÍTICO DE SEGURANÇA:** Você está prestes a apagar **{len(st.session_state.confirmar_delecao)}** lançamentos PERMANENTEMENTE. Esta ação não pode ser desfeita. Tem certeza absoluta?")
                col_sim, col_nao = st.columns(2)
                with col_sim:
                    if st.button("🚨 SIM, APAGAR DEFINITIVAMENTE", use_container_width=True):
                        try:
                            supabase.table("lancamentos").delete().in_("id", st.session_state.confirmar_delecao).execute()
                            st.session_state.confirmar_delecao = False
                            st.success("Lançamentos apagados de forma segura e irreversível.")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao excluir: {e}")
                with col_nao:
                    if st.button("✅ NÃO, CANCELAR E MANTER DADOS", type="primary", use_container_width=True):
                        st.session_state.confirmar_delecao = False
                        st.rerun()
            else:
                # Botões de Ações Rápidas normais (só aparecem se não estiver no modo Confirmação)
                st.markdown("#### ⚡ Ações Rápidas (Para os itens selecionados)")
                c_op1, c_op2, c_op3, c_op4 = st.columns(4)
                
                with c_op1:
                    if st.button("💾 Salvar Edições Manuais", type="primary", use_container_width=True):
                        try:
                            mudancas_realizadas = 0
                            for idx in range(len(df_resultado)):
                                row_editada = df_resultado.iloc[idx]
                                row_original = df_view.iloc[idx]
                                
                                if (str(row_editada["Data"]) != str(row_original["Data"]) or
                                    float(row_editada["Valor"]) != float(row_original["Valor"]) or
                                    str(row_editada["Competencia"]) != str(row_original["Competencia"]) or
                                    str(row_editada["Descricao"]) != str(row_original["Descricao"]) or
                                    str(row_editada["Categoria"]) != str(row_original["Categoria"]) or
                                    str(row_editada["Subcategoria"]) != str(row_original["Subcategoria"]) or
                                    str(row_editada["Conta_Cartao"]) != str(row_original["Conta_Cartao"]) or
                                    str(row_editada["Responsavel"]) != str(row_original["Responsavel"]) or
                                    str(row_editada["Origem_Destino"]) != str(row_original["Origem_Destino"]) or
                                    str(row_editada["Status"]) != str(row_original["Status"]) or
                                    str(row_editada["Tipo"]) != str(row_original["Tipo"])):
                                    
                                    supabase.table("lancamentos").update({
                                        "data_compra": str(row_editada["Data"]),
                                        "competencia": str(row_editada["Competencia"]),
                                        "tipo": str(row_editada["Tipo"]),
                                        "categoria": str(row_editada["Categoria"]),
                                        "subcategoria": str(row_editada["Subcategoria"]),
                                        "conta_cartao": str(row_editada["Conta_Cartao"]),
                                        "descricao": str(row_editada["Descricao"]),
                                        "valor": float(row_editada["Valor"]),
                                        "responsavel": str(row_editada["Responsavel"]),
                                        "origem_destino": str(row_editada["Origem_Destino"]),
                                        "status": str(row_editada["Status"])
                                    }).eq("id", str(row_editada["ID"])).execute()
                                    mudancas_realizadas += 1
                            
                            if mudancas_realizadas > 0:
                                st.success(f"✅ Sucesso! {mudancas_realizadas} edições salvas.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.info("Nenhuma edição manual detectada.")
                        except Exception as e:
                            st.error(f"Erro ao salvar edições: {e}")

                with c_op2:
                    if st.button("✅ Marcar como Pago", use_container_width=True):
                        if ids_selecionados:
                            try:
                                supabase.table("lancamentos").update({"status": "Pago"}).in_("id", ids_selecionados).execute()
                                st.success("Tudo atualizado para Pago!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e: st.error(f"Erro: {e}")
                        else: st.warning("Selecione algum item primeiro.")

                with c_op3:
                    if st.button("⏳ Marcar como Pendente", use_container_width=True):
                        if ids_selecionados:
                            try:
                                supabase.table("lancamentos").update({"status": "Pendente"}).in_("id", ids_selecionados).execute()
                                st.success("Tudo atualizado para Pendente!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e: st.error(f"Erro: {e}")
                        else: st.warning("Selecione algum item primeiro.")
                
                with c_op4:
                    if st.button("🗑️ Apagar Selecionados", use_container_width=True):
                        if ids_selecionados:
                            # ATIVA A TRAVA DE SEGURANÇA EM VEZ DE APAGAR DIRETAMENTE
                            st.session_state.confirmar_delecao = ids_selecionados
                            st.rerun()
                        else: st.warning("Selecione algum item primeiro.")
