# Importação das bibliotecas necessárias
import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------------
# Define o título da aba do navegador e o layout para ocupar toda a tela
st.set_page_config(page_title="Controle Financeiro ERP", layout="wide")

# ---------------------------------------------------------
# 2. BANCO DE DADOS VIRTUAL (SESSÃO)
# ---------------------------------------------------------
# Verifica se já existe uma tabela de dados na memória. Se não, cria uma tabela vazia.
if 'dados_financeiros' not in st.session_state:
    st.session_state['dados_financeiros'] = pd.DataFrame(
        columns=['Data', 'Tipo', 'Descrição', 'Categoria', 'Valor', 'Status']
    )

# ---------------------------------------------------------
# 3. BARRA LATERAL: FORMULÁRIO DE LANÇAMENTO
# ---------------------------------------------------------
st.sidebar.header("📝 Novo Lançamento")
st.sidebar.write("Adicione suas contas a pagar ou receber.")

# Criamos um formulário para o utilizador preencher os dados
with st.sidebar.form(key='form_lancamento', clear_on_submit=True):
    tipo_conta = st.radio("Tipo de Conta", ["Receita (A Receber)", "Despesa (A Pagar)"])
    data_conta = st.date_input("Data do Vencimento/Pagamento", datetime.today())
    descricao = st.text_input("Descrição (Ex: Conta de Luz, Venda de Produto)")
    categoria = st.selectbox("Categoria", ["Alimentação", "Serviços", "Salário", "Impostos", "Outros"])
    valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    status = st.selectbox("Status", ["Pendente", "Pago"])
    
    # Botão para salvar
    submit_button = st.form_submit_button(label='Adicionar Lançamento')

# Lógica para salvar os dados quando o botão é clicado
if submit_button:
    # Cria uma nova linha com os dados preenchidos
    novo_lancamento = pd.DataFrame([{
        'Data': data_conta,
        'Tipo': "Receita" if "Receita" in tipo_conta else "Despesa",
        'Descrição': descricao,
        'Categoria': categoria,
        'Valor': valor,
        'Status': status
    }])
    # Adiciona a nova linha à nossa tabela principal na memória
    st.session_state['dados_financeiros'] = pd.concat(
        [st.session_state['dados_financeiros'], novo_lancamento], 
        ignore_index=True
    )
    st.sidebar.success("Lançamento adicionado com sucesso!")

# ---------------------------------------------------------
# 4. PAINEL PRINCIPAL (DASHBOARD)
# ---------------------------------------------------------
st.title("📊 Controle de Contas a Pagar e Receber")
st.write("Visão geral das suas finanças, inspirado na praticidade dos melhores ERPs.")

# Puxamos os dados da memória para facilitar os cálculos
df = st.session_state['dados_financeiros']

# Cálculos Matemáticos do Dashboard
total_receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
total_despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
saldo_atual = total_receitas - total_despesas

# Criamos 3 colunas para colocar os cartões de resumo lado a lado
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total de Receitas", value=f"R$ {total_receitas:.2f}")
with col2:
    st.metric(label="Total de Despesas", value=f"R$ {total_despesas:.2f}")
with col3:
    st.metric(label="Saldo Geral", value=f"R$ {saldo_atual:.2f}")

st.markdown("---") # Linha divisória visual

# ---------------------------------------------------------
# 5. TABELA DE EXTRATO (VISUALIZAÇÃO DE DADOS)
# ---------------------------------------------------------
st.subheader("📋 Tabela de Lançamentos")

if df.empty:
    st.info("Nenhum lançamento registado ainda. Use a barra lateral para adicionar.")
else:
    # Mostra a tabela na tela de forma bonita
    st.dataframe(df, use_container_width=True, hide_index=True)
