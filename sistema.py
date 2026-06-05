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
# 3. AUTENTICAÇÃO COM VERIFICAÇÃO EM TEMPO REAL
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
                    except: st.error("E-mail ou senha incorretos ou usuário inexistente no Supabase.")
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
                        except: st.error("Erro ao criar conta no Supabase Auth.")
                    else: st.warning("Por favor, informe seu primeiro nome.")
    st.stop()

# ========================================================
# 4. FUNÇÕES BASE E LISTAS
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
            return df
    except: pass
    return pd.DataFrame(columns=["ID", "Data", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status", "Origem_Destino"])

df = carregar_dados()

def obter_opcoes(coluna, lista_base):
    if not df.empty and coluna in df.columns:
        existentes = df[coluna].dropna().astype(str).unique().tolist()
        return sorted(list(set(lista_base + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])))
    return sorted(lista_base)

LISTA_RESPONSAVEIS_BASE = [st.session_state.user_nome, "Família", "Empresa"]
LISTA_BANCOS = ["Nubank", "Inter", "Itaú", "Bradesco", "Banco do Brasil", "Dinheiro/Pix"]
LISTA_CATEGORIAS = ["Alimentação", "Transporte", "Moradia", "Salário", "Lazer", "Saúde", "Educação", "Investimentos", "Outros"]

def gerar_pdf(df_mes, mes_selecionado):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"Relatorio Financeiro PRO - {mes_selecionado}", 0, 1, 'C')
    pdf.ln(5)
    t_rec = df_mes[df_mes["Tipo"] == "Receita"]["Valor"].sum()
    t_desp = df_mes[df_mes["Tipo"] == "Despesa"]["Valor"].sum()
    t_inv = df_mes[df_mes["Tipo"] == "Investimento"]["Valor"].sum()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "Resumo Executivo:", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    pdf.cell(190, 8, f"Total de Entradas: R$ {t_rec:.2f}", 0, 1, 'L')
    pdf.cell(190, 8, f"Total de Saidas: R$ {t_desp:.2f}", 0, 1, 'L')
    pdf.cell(190, 8, f"Total Investido: R$ {t_inv:.2f}", 0, 1, 'L')
    pdf.cell(190, 8, f"Saldo Final em Conta: R$ {(t_rec - t_desp - t_inv):.2f}", 0, 1, 'L')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "Ultimos Lancamentos do Mes:", 0, 1, 'L')
    pdf.set_font("Arial", '', 10)
    df_lista = df_mes.sort_values("Data", ascending=False).head(30)
    for index, row in df_lista.iterrows():
        desc = str(row['Descricao'])[:30] 
        linha_texto = f"{row['Data']} | {row['Tipo'][:4]} | {row['Categoria'][:15]} | {desc} | R$ {row['Valor']:.2f}"
        pdf.cell(190, 6, linha_texto, 0, 1, 'L')
    return pdf.output(dest="S").encode("latin-1")

# ========================================================
# 5. HEADER
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
# 6. DASHBOARD
# ========================================================
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        dash_mensal, dash_anual, dash_metas = st.tabs(["📅 Visão Mensal", "📈 Visão Anual", "🎯 Metas e Orçamentos"])
        with dash_mensal:
            col_filtro1, _ = st.columns(2)
            with col_filtro1:
                mes_selecionado = st.selectbox("Selecione o Mês", ["Ver Tudo"] + sorted(df["Competencia"].unique(), reverse=True))
            
            df_dash = df[df["Competencia"] == mes_selecionado] if mes_selecionado != "Ver Tudo" else df.copy()
            t_rec = df_dash[df_dash["Tipo"] == "Receita"]["Valor"].sum()
            t_desp = df_dash[df_dash["Tipo"] == "Despesa"]["Valor"].sum()
            t_inv = df_dash[df_dash["Tipo"] == "Investimento"]["Valor"].sum()
            saldo_liquido = t_rec - t_desp - t_inv
            
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="executive-box" style="border-top: 4px solid #0284C7;"><div class="term-label">Saldo Conta (Sobra)</div><div class="term-amount" style="color:#0284C7;">R$ {saldo_liquido:,.2f}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="executive-box" style="border-top: 4px solid #16A34A;"><div class="term-label">Entradas (+)</div><div class="term-amount" style="color:#16A34A;">R$ {t_rec:,.2f}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="executive-box" style="border-top: 4px solid #DC2626;"><div class="term-label">Saídas (-)</div><div class="term-amount" style="color:#DC2626;">R$ {t_desp:,.2f}</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="executive-box" style="border-top: 4px solid #8B5CF6;"><div class="term-label">Investido (💼)</div><div class="term-amount" style="color:#8B5CF6;">R$ {t_inv:,.2f}</div></div>', unsafe_allow_html=True)
            
            if t_desp > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_graf1, col_graf2 = st.columns(2)
                with col_graf1: 
                    st.plotly_chart(px.pie(df_dash[df_dash["Tipo"] == "Despesa"], values="Valor", names="Categoria", title="Distribuição de Despesas"), use_container_width=True)
                with col_graf2: 
                    st.plotly_chart(px.bar(df_dash[df_dash["Tipo"] == "Despesa"].groupby("Descricao")["Valor"].sum().reset_index().sort_values("Valor", ascending=False).head(5), x="Valor", y="Descricao", orientation='h', title="Top 5 Maiores Gastos"), use_container_width=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_graf3, col_graf4 = st.columns(2)
                with col_graf3:
                    df_resp = df_dash[df_dash["Tipo"] == "Despesa"].groupby("Responsavel")["Valor"].sum().reset_index()
                    st.plotly_chart(px.pie(df_resp, values="Valor", names="Responsavel", title="Gastos por Responsável (Quem Pagou)"), use_container_width=True)
                with col_graf4:
                    df_dest = df_dash[(df_dash["Tipo"] == "Despesa") & (df_dash["Origem_Destino"] != "")]
                    if not df_dest.empty:
                        df_dest_agrupado = df_dest.groupby("Origem_Destino")["Valor"].sum().reset_index().sort_values("Valor", ascending=False).head(5)
                        st.plotly_chart(px.bar(df_dest_agrupado, x="Valor", y="Origem_Destino", orientation='h', title="Top 5 Recebedores (Para onde foi o dinheiro)"), use_container_width=True)
                    else:
                        st.info("💡 Adicione o local de Origem/Destino nos seus lançamentos para gerar este ranking.")

            st.markdown("---")
            try:
                pdf_bytes = gerar_pdf(df_dash, str(mes_selecionado))
                st.download_button(label="📄 Baixar Relatório em PDF", data=pdf_bytes, file_name=f"Relatorio_Financeiro_{mes_selecionado}.pdf", mime="application/pdf", type="primary")
            except: st.warning("Processando gerador de PDF...")
        
        with dash_anual:
            st.plotly_chart(px.bar(df.groupby(["Competencia", "Tipo"])["Valor"].sum().reset_index(), x="Competencia", y="Valor", color="Tipo", barmode="group", title="Evolução Mensal", color_discrete_map={"Receita": "#16A34A", "Despesa": "#DC2626", "Investimento": "#8B5CF6"}), use_container_width=True)
            
        with dash_metas:
            c_meta1, c_meta2 = st.columns([1, 2])
            with c_meta1:
                with st.container(border=True):
                    st.markdown("#### Nova Meta")
                    cat_meta = st.selectbox("Escolha a Categoria", obter_opcoes("Categoria", LISTA_CATEGORIAS))
                    limite_meta = st.number_input("Limite Máximo (R$)", min_value=0.0, value=500.0, step=50.0)
                    if st.button("Salvar Meta", type="primary", use_container_width=True):
                        st.session_state.orcamentos[cat_meta] = limite_meta
                        st.success(f"Meta para {cat_meta} registrada!")
                        time.sleep(1)
                        st.rerun()
            with c_meta2:
                mes_atual_metas = datetime.now().strftime("%Y-%m")
                st.markdown(f"#### Termômetro do Mês ({mes_atual_metas})")
                df_mes_metas = df[(df["Competencia"] == mes_atual_metas) & (df["Tipo"] == "Despesa")]
                if not st.session_state.orcamentos: st.info("💡 Você ainda não possui metas definidas. Crie uma meta ao lado.")
                else:
                    for cat, limite in st.session_state.orcamentos.items():
                        gasto_atual = df_mes_metas[df_mes_metas["Categoria"] == cat]["Valor"].sum()
                        percentual = min(gasto_atual / limite, 1.0) if limite > 0 else 1.0 if gasto_atual > 0 else 0.0
                        st.write(f"**{cat}**: R$ {gasto_atual:,.2f} de R$ {limite:,.2f}")
                        st.progress(percentual)
                        if percentual >= 1.0: st.error("🚨 Orçamento estourado nesta categoria!")
                        elif percentual >= 0.8: st.warning("⚠️ Atenção! Perto do limite.")
                        st.markdown("---")
    else: st.info("O Dashboard aguarda lançamentos.")

# ========================================================
# 7. LANÇAMENTOS E EDIÇÃO EM MASSA (COM FILTROS)
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
            c4, c5, c6 = st.columns(3)
            with c4:
                opcoes_cat = obter_opcoes("Categoria", LISTA_CATEGORIAS) + ["➕ Nova Categoria..."]
                cat_sel = st.selectbox("Categoria", opcoes_cat)
                categoria = st.text_input("Nome da Nova Categoria:") if cat_sel == "➕ Nova Categoria..." else cat_sel
            with c5:
                opcoes_conta = obter_opcoes("Conta_Cartao", LISTA_BANCOS) + ["➕ Nova Conta..."]
                conta_sel = st.selectbox("Conta / Cartão", opcoes_conta)
                conta_cartao = st.text_input("Nome da Nova Conta:") if conta_sel == "➕ Nova Conta..." else conta_sel
            with c6:
                opcoes_orig = obter_opcoes("Origem_Destino", ["Supermercado", "Pix", "Empresa"]) + ["➕ Nova Origem/Destino..."]
                orig_sel = st.selectbox("Origem / Destino (Ex: Estabelecimento)", opcoes_orig)
                origem_destino = st.text_input("Nome da Nova Origem/Destino:") if orig_sel == "➕ Nova Origem/Destino..." else orig_sel

        with st.container(border=True):
            st.markdown("#### 3. Detalhes Adicionais")
            c7, c8, c9, c10 = st.columns(4)
            with c7:
                opcoes_resp = obter_opcoes("Responsavel", LISTA_RESPONSAVEIS_BASE) + ["➕ Novo Responsável..."]
                resp_sel = st.selectbox("Responsável (Quem paga/pagou)", opcoes_resp)
                responsavel = st.text_input("Nome do Responsável:") if resp_sel == "➕ Novo Responsável..." else resp_sel
            with c8: descricao = st.text_input("Descrição Resumida")
            
            with c9: ano_comp = st.selectbox("Ano Competência", [2026, 2027, 2028])
            with c10:
                meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
                mes_sel = st.selectbox("Mês Competência (Fatura)", meses_nomes, index=datetime.now().month - 1)
                mes_num = mes_sel.split(" - ")[0]
                competencia_final = f"{ano_comp}-{mes_num}"
                
            st.markdown("---")
            modo_lancamento = st.radio("Frequência de Lançamento:", ["Único (À vista)", "Parcelado", "Assinatura Mensal"], horizontal=True)
            if modo_lancamento == "Parcelado": parcelas = st.number_input("Número de Parcelas", min_value=2, max_value=120, value=2)
            elif modo_lancamento == "Assinatura Mensal": parcelas = st.number_input("Projetar por quantos meses?", min_value=2, max_value=60, value=12)
            else: parcelas = 1

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Concluir Lançamento no Sistema", type="primary", use_container_width=True):
            if valor_total > 0 and categoria and conta_cartao and responsavel:
                novas_linhas = []
                valor_por_mes = valor_total / parcelas if modo_lancamento == "Parcelado" else valor_total
                start_year = ano_comp
                start_month = int(mes_num)
                
                for i in range(parcelas):
                    m = start_month - 1 + i
                    y = start_year + (m // 12)
                    comp = f"{y}-{(m % 12) + 1:02d}"
                    origem_segura = origem_destino if origem_destino else ""
                    nova_data_compra = (pd.to_datetime(data_compra) + pd.DateOffset(months=i)).strftime("%Y-%m-%d")
                    
                    novas_linhas.append({"user_email": st.session_state.user_email, "data_compra": nova_data_compra, "competencia": comp, "tipo": tipo, "categoria": categoria, "subcategoria": "Geral", "conta_cartao": conta_cartao, "valor": float(round(valor_por_mes, 2)), "descricao": descricao, "parcela": f"{i+1}/{parcelas}" if modo_lancamento == "Parcelado" else "Recorrente" if modo_lancamento == "Assinatura Mensal" else "À vista", "responsavel": responsavel, "origem_destino": origem_segura, "status": "Pago" if i == 0 else "Pendente"})
                try:
                    supabase.table("lancamentos").insert(novas_linhas).execute()
                    st.success("Registrado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
            else: st.warning("Preencha os dados base.")

    with aba_importar:
        st.subheader("Integração Inteligente de Faturas")
        arquivo = st.file_uploader("Anexe sua fatura CSV/Excel", type=["csv", "xlsx", "xls"])
        if arquivo:
            df_fatura = pd.read_csv(arquivo, sep=None, engine='python') if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
            df_fatura["Categoria_Sistema"] = "Outros"
            df_fatura["Tipo_Sistema"] = "Despesa"
            c1, c2, c3 = st.columns(3)
            col_data = c1.selectbox("Coluna Data?", df_fatura.columns)
            col_desc = c2.selectbox("Coluna Descrição?", df_fatura.columns)
            col_valor = c3.selectbox("Coluna Valor?", df_fatura.columns)
            df_editado = st.data_editor(df_fatura, num_rows="dynamic", use_container_width=True)
            if st.button("🚀 Salvar Fatura", type="primary"):
                novas_linhas = []
                for index, row in df_editado.iterrows():
                    try: val = float(str(row[col_valor]).replace('R$', '').replace('.', '').replace(',', '.').strip())
                    except: val = 0.0
                    if val != 0: novas_linhas.append({"user_email": st.session_state.user_email, "data_compra": str(row[col_data])[:10], "competencia": datetime.now().strftime("%Y-%m"), "tipo": row.get("Tipo_Sistema", "Despesa"), "categoria": row.get("Categoria_Sistema", "Outros"), "conta_cartao": "Importado", "valor": abs(val), "descricao": str(row[col_desc]), "parcela": "Fatura", "responsavel": "Eu", "origem_destino": "", "status": "Pago"})
                if novas_linhas:
                    supabase.table("lancamentos").insert(novas_linhas).execute()
                    st.success("Importado!")
                    time.sleep(1)
                    st.rerun()

    # ========================================================
    # ATUALIZAÇÃO PREMIUM: FILTROS INTELIGENTES ANTES DE EDITAR
    # ========================================================
    with aba_gerenciar:
        st.markdown("### ✏️ Mesa de Operações: Edição Visual e Exclusão em Massa")
        if df.empty:
            st.info("Nenhum lançamento encontrado para gerenciar.")
        else:
            # Prepara a base de visualização
            df_view = df[["ID", "Data", "Competencia", "Tipo", "Categoria", "Conta_Cartao", "Descricao", "Valor", "Responsavel", "Origem_Destino"]].copy()
            df_view.insert(0, "Apagar?", False)
            
            # Painel de Filtros Inteligentes
            st.markdown("#### 🔍 Filtros de Busca")
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                opcoes_tipo = ["Todos", "Despesa", "Receita", "Investimento"]
                filtro_tipo = st.selectbox("Filtrar por Tipo", opcoes_tipo)
            with c_f2:
                opcoes_comp = ["Todos"] + sorted(df_view["Competencia"].unique(), reverse=True)
                filtro_comp = st.selectbox("Filtrar por Competência", opcoes_comp)
            with c_f3:
                opcoes_cat = ["Todas"] + sorted(df_view["Categoria"].unique())
                filtro_cat = st.selectbox("Filtrar por Categoria", opcoes_cat)
            
            # Aplica os filtros na tabela antes de mostrá-la
            if filtro_tipo != "Todos":
                df_view = df_view[df_view["Tipo"] == filtro_tipo]
            if filtro_comp != "Todos":
                df_view = df_view[df_view["Competencia"] == filtro_comp]
            if filtro_cat != "Todas":
                df_view = df_view[df_view["Categoria"] == filtro_cat]
            
            st.write(f"🔒 **Instruções Dinâmicas:** Mostrando {len(df_view)} lançamentos. Edite os dados na tabela e clique em **'Salvar Edições'**. Para excluir, marque as caixas na coluna **'Apagar?'**.")
            
            # Editor renderiza apenas os dados filtrados
            df_resultado = st.data_editor(
                df_view, 
                hide_index=True, 
                use_container_width=True, 
                disabled=["ID"] 
            )
            
            ids_para_apagar = df_resultado[df_resultado["Apagar?"] == True]["ID"].tolist()
            
            c_op1, c_op2 = st.columns(2)
            with c_op1:
                if st.button("💾 Salvar Edições da Tabela", type="primary", use_container_width=True):
                    try:
                        mudancas_realizadas = 0
                        # O loop agora compara linha a linha do resultado filtrado com a visualização filtrada original
                        for idx in range(len(df_resultado)):
                            row_editada = df_resultado.iloc[idx]
                            row_original = df_view.iloc[idx]
                            
                            if not row_editada["Apagar?"]:
                                if (str(row_editada["Data"]) != str(row_original["Data"]) or
                                    float(row_editada["Valor"]) != float(row_original["Valor"]) or
                                    str(row_editada["Competencia"]) != str(row_original["Competencia"]) or
                                    str(row_editada["Descricao"]) != str(row_original["Descricao"]) or
                                    str(row_editada["Categoria"]) != str(row_original["Categoria"]) or
                                    str(row_editada["Conta_Cartao"]) != str(row_original["Conta_Cartao"]) or
                                    str(row_editada["Responsavel"]) != str(row_original["Responsavel"]) or
                                    str(row_editada["Origem_Destino"]) != str(row_original["Origem_Destino"]) or
                                    str(row_editada["Tipo"]) != str(row_original["Tipo"])):
                                    
                                    supabase.table("lancamentos").update({
                                        "data_compra": str(row_editada["Data"]),
                                        "competencia": str(row_editada["Competencia"]),
                                        "tipo": str(row_editada["Tipo"]),
                                        "categoria": str(row_editada["Categoria"]),
                                        "conta_cartao": str(row_editada["Conta_Cartao"]),
                                        "descricao": str(row_editada["Descricao"]),
                                        "valor": float(row_editada["Valor"]),
                                        "responsavel": str(row_editada["Responsavel"]),
                                        "origem_destino": str(row_editada["Origem_Destino"])
                                    }).eq("id", str(row_editada["ID"])).execute()
                                    mudancas_realizadas += 1
                        
                        if mudancas_realizadas > 0:
                            st.success(f"✅ Sucesso! {mudancas_realizadas} lançamentos atualizados.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.info("Nenhuma edição detectada.")
                    except Exception as e:
                        st.error(f"Erro ao salvar edições: {e}")
            
            with c_op2:
                if ids_para_apagar:
                    if st.button(f"🗑️ Apagar {len(ids_para_apagar)} Selecionados", use_container_width=True):
                        try:
                            supabase.table("lancamentos").delete().in_("id", ids_para_apagar).execute()
                            st.error("Lançamentos Removidos!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao excluir: {e}")

# ========================================================
# 8. ASSISTENTE IA 
# ========================================================
with aba_assistente:
    st.markdown("### 🤖 Cérebro Digital - Inteligência Autoral")
    boas_vindas = f"Olá, {st.session_state.user_nome}! Pergunte sobre faturas, períodos ou gastos do seu histórico."
    
    if modelo_ia:
        if "mensagens_chat" not in st.session_state: 
            st.session_state.mensagens_chat = [{"role": "assistant", "content": boas_vindas}]
        for msg in st.session_state.mensagens_chat:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
        prompt = st.chat_input("Consulte sua base de dados inteligente...")
        if prompt:
            st.session_state.mensagens_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Processando dados internos..."):
                    try:
                        hist_txt = df[["Data", "Tipo", "Categoria", "Conta_Cartao", "Responsavel", "Origem_Destino", "Descricao", "Valor"]].to_string(index=False) if not df.empty else "Vazio."
                        prompt_final = f"Atue como o motor financeiro de {st.session_state.user_nome}. Faça somas matemáticas se pedido datas (dia 1 ao 5) ou nomes (iFood).\n\nDADOS:\n{hist_txt}\nPERGUNTA: {prompt}"
                        resposta = modelo_ia.generate_content(prompt_final)
                        st.markdown(resposta.text)
                        st.session_state.mensagens_chat.append({"role": "assistant", "content": resposta.text})
                    except Exception as e: st.error(f"Erro de IA: {e}")

# ========================================================
# 9. OPEN FINANCE
# ========================================================
with aba_openfinance:
    st.subheader("🔌 Hub de Integração Bancária")
    if "banco_conectado" not in st.session_state: st.session_state.banco_conectado = False
    if not st.session_state.banco_conectado:
        if st.button("🚀 Simular Conexão (Bypass)", type="primary"):
            st.session_state.banco_conectado = True
            st.session_state.item_id_simulado = f"item_sandbox_{int(time.time())}"
            st.rerun()
    else:
        st.markdown(f"<div class='status-box'>🎉 MÁGICA CONCLUÍDA!<br><br>Item ID: {st.session_state.item_id_simulado}</div>", unsafe_allow_html=True)
        if st.button("🔴 Desconectar Conta"):
            st.session_state.banco_conectado = False
            st.rerun()
