import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from supabase_manager import SupabaseManager
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Sistema de Orçamentos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do Supabase
@st.cache_resource
def get_database():
    return SupabaseManager()

db = get_database()

# Função de autenticação
def check_authentication():
    """Verifica se o usuário está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Login - Sistema Touché")
        st.markdown("---")
        
        # Formulário de login
        with st.form("login_form"):
            st.subheader("Acesse o Sistema")
            
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("🔑 Entrar")
            with col2:
                if st.form_submit_button("❌ Cancelar"):
                    st.stop()
            
            if submitted:
                # Usar o Supabase Manager para autenticação
                auth_result = db.autenticar_usuario(username, password)
                
                if auth_result['success']:
                    st.session_state.authenticated = True
                    st.session_state.username = auth_result['user']['email']
                    st.session_state.user_role = auth_result['user']['role']
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"❌ {auth_result['error']}")        
        st.stop()
    
    return True

# Verificar autenticação
check_authentication()

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("📋 Menu")

# Informações do usuário logado
if 'username' in st.session_state:
    user_role = st.session_state.get('user_role', 'user')
    if user_role == 'admin':
        role_display = "👑 Administrador"
    elif user_role == 'atendimento':
        role_display = "👩 Atendimento"
    else:
        role_display = "👤 Usuário"
    st.sidebar.success(f"{role_display}: {st.session_state.username}")

# Definir páginas disponíveis baseado no perfil
if 'user_role' in st.session_state:
    if st.session_state.user_role == 'admin':
        # Administrador tem acesso a tudo
        paginas_disponiveis = [
            "🏠 Dashboard", 
            "👥 Clientes", 
            "📦 Produtos", 
            "💰 Novo Orçamento", 
            "📊 Orçamentos", 
            "📈 Relatórios"
        ]
    elif st.session_state.user_role == 'atendimento':
        # Atendimento tem acesso apenas a clientes
        paginas_disponiveis = [
            "👥 Clientes"
        ]
    else:
        # Usuário comum tem acesso limitado
        paginas_disponiveis = [
            "🏠 Dashboard", 
            "👥 Clientes", 
            "📦 Produtos"
        ]
else:
    # Fallback para usuários sem perfil definido
    paginas_disponiveis = ["🏠 Dashboard", "👥 Clientes"]

pagina = st.sidebar.selectbox(
    "Selecione a página:",
    paginas_disponiveis
)

# Botão de logout
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    if 'username' in st.session_state:
        del st.session_state.username
    st.success("✅ Logout realizado com sucesso!")
    st.rerun()

# Função para exibir dashboard
def dashboard():
    st.markdown('<h1 class="main-header">Sistema de Orçamentos</h1>', unsafe_allow_html=True)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        clientes_df = db.buscar_clientes()
        st.metric("Total de Clientes", len(clientes_df))
    
    with col2:
        produtos_df = db.buscar_produtos()
        st.metric("Total de Produtos", len(produtos_df))
    
    with col3:
        orcamentos_df = db.buscar_orcamentos()
        st.metric("Total de Orçamentos", len(orcamentos_df))
    
    with col4:
        if not orcamentos_df.empty:
            total_vendas = orcamentos_df['total'].sum()
            st.metric("Total em Vendas", f"R$ {total_vendas:,.2f}")
        else:
            st.metric("Total em Vendas", "R$ 0,00")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        if not orcamentos_df.empty:
            # Gráfico de orçamentos por mês
            orcamentos_df['data_orcamento'] = pd.to_datetime(orcamentos_df['data_orcamento'])
            orcamentos_df['mes'] = orcamentos_df['data_orcamento'].dt.strftime('%Y-%m')
            orcamentos_por_mes = orcamentos_df.groupby('mes').size().reset_index(name='quantidade')
            
            fig = px.line(orcamentos_por_mes, x='mes', y='quantidade', 
                         title='Orçamentos por Mês', markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not orcamentos_df.empty:
            # Gráfico de status dos orçamentos
            status_counts = orcamentos_df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title='Status dos Orçamentos')
            st.plotly_chart(fig, use_container_width=True)
    
    # Últimos orçamentos
    st.subheader("📋 Últimos Orçamentos")
    if not orcamentos_df.empty:
        ultimos_orcamentos = orcamentos_df.head(5)[['numero_orcamento', 'cliente_nome', 'total', 'status', 'data_orcamento']]
        st.dataframe(ultimos_orcamentos, use_container_width=True)
    else:
        st.info("Nenhum orçamento encontrado.")

# Função para gerenciar clientes
def formatar_cpf_cnpj(cpf_cnpj, tipo_pessoa):
    """Formata CPF/CNPJ baseado no tipo de pessoa"""
    if not cpf_cnpj or pd.isna(cpf_cnpj) or cpf_cnpj == '':
        return '-'
    
    # Remove caracteres não numéricos
    numeros = ''.join(filter(str.isdigit, str(cpf_cnpj)))
    
    if tipo_pessoa == 'fisica':
        # Formata CPF: XXX.XXX.XXX-XX
        if len(numeros) == 11:
            return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
        else:
            return cpf_cnpj
    elif tipo_pessoa == 'juridica':
        # Formata CNPJ: XX.XXX.XXX/XXXX-XX
        if len(numeros) == 14:
            return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
        else:
            return cpf_cnpj
    else:
        return cpf_cnpj

def clientes():
    st.title("👥 Touché - Cadastro de Clientes")
    st.markdown("Aplicação Streamlit para cadastro e gerenciamento de clientes da Touché.")
    
    # Definir abas baseado no perfil do usuário
    if 'user_role' in st.session_state and (st.session_state.user_role == 'admin' or st.session_state.user_role == 'atendimento'):
        # Administrador e Atendimento têm acesso a todas as abas de clientes
        tab1, tab2, tab3 = st.tabs(["📝 Cadastrar Cliente", "📋 Lista de Clientes", "🔍 Buscar Cliente"])
    else:
        # Usuário comum só pode visualizar e buscar
        tab1, tab2 = st.tabs(["📋 Lista de Clientes", "🔍 Buscar Cliente"])
    
    # Aba de cadastro (para admin e atendimento)
    if 'user_role' in st.session_state and (st.session_state.user_role == 'admin' or st.session_state.user_role == 'atendimento'):
        with tab1:
            st.subheader("Novo Cliente")
            
            with st.form("novo_cliente"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nome = st.text_input("Nome/Razão Social *", placeholder="Ex: João Silva ou Empresa ABC Ltda")
                    contato = st.text_input("Contato *", placeholder="Ex: (11) 99999-9999")
                    representante = st.text_input("Representante (opcional)", placeholder="Ex: Maria Silva")
                
                with col2:
                    email = st.text_input("Email *", placeholder="Ex: joao@email.com")
                    inscricao = st.text_input("CPF/CNPJ (opcional)", placeholder="Ex: 123.456.789-01 ou 12.345.678/0001-90")
                    pessoa = st.selectbox("Tipo de Pessoa *", ["fisica", "juridica"], format_func=lambda x: "Pessoa Física" if x == "fisica" else "Pessoa Jurídica")
                
                submitted = st.form_submit_button("Cadastrar Cliente")
                
                if submitted:
                    # Validações
                    erros = []
                    
                    # Validação do nome
                    if not nome or nome.strip() == "":
                        erros.append("Nome/Razão Social é obrigatório")
                    elif len(nome.strip()) < 3:
                        erros.append("Nome/Razão Social deve ter pelo menos 3 caracteres")
                    
                    # Validação do contato
                    if not contato or contato.strip() == "":
                        erros.append("Contato é obrigatório")
                    elif len(contato.strip()) < 8:
                        erros.append("Contato deve ter pelo menos 8 caracteres")
                    
                    # Validação do email
                    if not email or email.strip() == "":
                        erros.append("Email é obrigatório")
                    else:
                        email_limpo = email.strip()
                        if not '@' in email_limpo or not '.' in email_limpo:
                            erros.append("Email deve ter formato válido")
                        elif len(email_limpo) < 5:
                            erros.append("Email deve ter pelo menos 5 caracteres")
                        elif email_limpo.count('@') != 1:
                            erros.append("Email deve conter exatamente um @")
                        elif email_limpo.startswith('@') or email_limpo.endswith('@'):
                            erros.append("Email não pode começar ou terminar com @")
                        elif email_limpo.startswith('.') or email_limpo.endswith('.'):
                            erros.append("Email não pode começar ou terminar com ponto")
                    
                    # Validação de CPF/CNPJ baseada no tipo de pessoa
                    if inscricao and inscricao.strip() != "":
                        inscricao_limpa = inscricao.replace('.', '').replace('-', '').replace('/', '').strip()
                        
                        # Verificar se contém apenas números
                        if not inscricao_limpa.isdigit():
                            erros.append("CPF/CNPJ deve conter apenas números")
                        else:
                            if pessoa == "fisica":
                                if len(inscricao_limpa) != 11:
                                    erros.append("CPF deve ter 11 dígitos para pessoa física")
                                else:
                                    # Validação básica de CPF (soma dos dígitos)
                                    if inscricao_limpa == inscricao_limpa[0] * 11:
                                        erros.append("CPF não pode ter todos os dígitos iguais")
                            elif pessoa == "juridica":
                                if len(inscricao_limpa) != 14:
                                    erros.append("CNPJ deve ter 14 dígitos para pessoa jurídica")
                                else:
                                    # Validação básica de CNPJ (soma dos dígitos)
                                    if inscricao_limpa == inscricao_limpa[0] * 14:
                                        erros.append("CNPJ não pode ter todos os dígitos iguais")
                    
                    # Validação do representante (se preenchido)
                    if representante and representante.strip() != "":
                        if len(representante.strip()) < 2:
                            erros.append("Representante deve ter pelo menos 2 caracteres")
                    
                    if erros:
                        for erro in erros:
                            st.error(erro)
                    else:
                        # Inserir cliente
                        cliente_id = db.inserir_cliente(
                            nome=nome.strip(),
                            email=email.strip(),
                            telefone=contato.strip(),
                            cpf_cnpj=inscricao.strip() if inscricao else "",
                            endereco=f"Representante: {representante.strip()}" if representante and representante.strip() else "",
                            pessoa=pessoa
                        )
                        if cliente_id:
                            st.success(f"Cliente '{nome.strip()}' cadastrado com sucesso! ID: {cliente_id}")
                        else:
                            st.error("Erro ao cadastrar cliente. Tente novamente.")
    
    with tab2:
        st.subheader("Clientes Cadastrados")
        clientes_df = db.buscar_clientes()
        
        if not clientes_df.empty:
            # Formatar CPF/CNPJ baseado no tipo de pessoa
            clientes_df['cpf_cnpj_formatado'] = clientes_df.apply(
                lambda row: formatar_cpf_cnpj(row['cpf_cnpj'], row['pessoa']), 
                axis=1
            )
            
            # Selecionar apenas as colunas necessárias
            colunas_exibicao = ['id', 'nome', 'email', 'telefone', 'cpf_cnpj_formatado', 'representante']
            clientes_df_exibicao = clientes_df[colunas_exibicao].copy()
            
            # Renomear colunas para melhor visualização
            clientes_df_exibicao = clientes_df_exibicao.rename(columns={
                'id': 'ID',
                'nome': 'Nome/Razão Social',
                'email': 'Email',
                'telefone': 'Contato',
                'cpf_cnpj_formatado': 'CPF/CNPJ',
                'representante': 'Representante'
            })
            
            st.dataframe(clientes_df_exibicao, use_container_width=True, hide_index=True)
            
            # Download dos dados
            csv = clientes_df_exibicao.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="clientes_touche.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhum cliente cadastrado ainda.")
    
    with tab3:
        st.subheader("Buscar Cliente")
        
        busca = st.text_input("Digite nome, email, CPF ou CNPJ:", placeholder="Ex: João, joao@email.com, 123.456.789-01")
        
        if busca:
            clientes_df = db.buscar_clientes()
            
            if not clientes_df.empty:
                # Filtrar resultados
                mask = (
                    clientes_df['nome'].str.contains(busca, case=False, na=False) |
                    clientes_df['email'].str.contains(busca, case=False, na=False) |
                    clientes_df['cpf_cnpj'].str.contains(busca, case=False, na=False)
                )
                
                resultados = clientes_df[mask]
                
                if not resultados.empty:
                    st.success(f"Encontrados {len(resultados)} cliente(s)")
                    
                    # Formatar CPF/CNPJ baseado no tipo de pessoa
                    resultados['cpf_cnpj_formatado'] = resultados.apply(
                        lambda row: formatar_cpf_cnpj(row['cpf_cnpj'], row['pessoa']), 
                        axis=1
                    )
                    
                    # Selecionar apenas as colunas necessárias
                    colunas_exibicao = ['id', 'nome', 'email', 'telefone', 'cpf_cnpj_formatado', 'representante']
                    resultados_exibicao = resultados[colunas_exibicao].copy()
                    
                    # Renomear colunas
                    resultados_exibicao = resultados_exibicao.rename(columns={
                        'id': 'ID',
                        'nome': 'Nome/Razão Social',
                        'email': 'Email',
                        'telefone': 'Contato',
                        'cpf_cnpj_formatado': 'CPF/CNPJ',
                        'representante': 'Representante'
                    })
                    
                    st.dataframe(resultados_exibicao, use_container_width=True, hide_index=True)
                else:
                    st.warning("Nenhum cliente encontrado com os critérios informados.")
            else:
                st.info("Nenhum cliente cadastrado ainda.")

# Função para gerenciar produtos
def produtos():
    # Verificar permissão
    if 'user_role' in st.session_state and st.session_state.user_role != 'admin':
        st.warning("⚠️ Acesso restrito. Apenas administradores podem gerenciar produtos.")
        st.info("Entre em contato com o administrador para solicitar acesso.")
        return
    
    st.title("📦 Gerenciamento de Produtos")
    
    tab1, tab2 = st.tabs(["📝 Cadastrar Produto", "📋 Lista de Produtos"])
    
    with tab1:
        st.subheader("Novo Produto/Serviço")
        
        with st.form("novo_produto"):
            nome = st.text_input("Nome do produto/serviço *")
            descricao = st.text_area("Descrição")
            preco_unitario = st.number_input("Preço unitário (R$) *", min_value=0.0, value=0.0, step=0.01)
            categoria = st.text_input("Categoria")
            
            submitted = st.form_submit_button("Cadastrar Produto")
            
            if submitted:
                if nome and preco_unitario >= 0:
                    produto_id = db.inserir_produto(nome, descricao, preco_unitario, categoria)
                    st.success(f"Produto '{nome}' cadastrado com sucesso! ID: {produto_id}")
                else:
                    st.error("Nome e preço são obrigatórios!")
    
    with tab2:
        st.subheader("Produtos Cadastrados")
        produtos_df = db.buscar_produtos()
        
        if not produtos_df.empty:
            # Verificar se a coluna data_cadastro existe
            if 'data_cadastro' in produtos_df.columns:
                # Formatação da data
                produtos_df['data_cadastro'] = pd.to_datetime(produtos_df['data_cadastro']).dt.strftime('%d/%m/%Y %H:%M')
            else:
                # Se não existir, criar uma coluna vazia
                produtos_df['data_cadastro'] = 'N/A'
            
            # Formatação do preço
            produtos_df['preco_unitario'] = produtos_df['preco_unitario'].apply(lambda x: f"R$ {x:.2f}")
            
            st.dataframe(produtos_df, use_container_width=True)
            
            # Download dos dados
            csv = produtos_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="produtos.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhum produto cadastrado ainda.")

# Função para criar novo orçamento
def novo_orcamento():
    # Verificar permissão
    if 'user_role' in st.session_state and st.session_state.user_role != 'admin':
        st.warning("⚠️ Acesso restrito. Apenas administradores podem criar orçamentos.")
        st.info("Entre em contato com o administrador para solicitar acesso.")
        return
    
    st.title("💰 Novo Orçamento")
    
    # Buscar dados necessários
    clientes_df = db.buscar_clientes()
    produtos_df = db.buscar_produtos()
    
    if clientes_df.empty:
        st.error("É necessário cadastrar pelo menos um cliente antes de criar orçamentos.")
        return
    
    if produtos_df.empty:
        st.error("É necessário cadastrar pelo menos um produto antes de criar orçamentos.")
        return
    
    with st.form("novo_orcamento"):
        st.subheader("Informações do Orçamento")
        
        # Seleção do cliente
        cliente_options = {f"{row['nome']} (ID: {row['id']})": row['id'] for _, row in clientes_df.iterrows()}
        cliente_selecionado = st.selectbox("Cliente *", options=list(cliente_options.keys()), required=True)
        cliente_id = cliente_options[cliente_selecionado]
        
        # Data de validade
        data_validade = st.date_input("Data de validade", value=datetime.now() + timedelta(days=30))
        
        # Observações
        observacoes = st.text_area("Observações")
        
        st.subheader("Itens do Orçamento")
        
        # Lista de itens
        itens = []
        
        # Criar campos para itens
        num_itens = st.number_input("Número de itens", min_value=1, max_value=20, value=1)
        
        for i in range(num_itens):
            st.write(f"--- Item {i+1} ---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                produto_options = {f"{row['nome']} - R$ {row['preco_unitario']:.2f}": row['id'] for _, row in produtos_df.iterrows()}
                produto_selecionado = st.selectbox(f"Produto {i+1}", options=list(produto_options.keys()), key=f"produto_{i}")
                produto_id = produto_options[produto_selecionado]
            
            with col2:
                quantidade = st.number_input(f"Quantidade {i+1}", min_value=0.01, value=1.0, step=0.01, key=f"qtd_{i}")
            
            with col3:
                preco_unitario = st.number_input(f"Preço unitário {i+1}", min_value=0.0, value=0.0, step=0.01, key=f"preco_{i}")
            
            # Calcular subtotal do item
            subtotal_item = quantidade * preco_unitario
            st.write(f"**Subtotal do item {i+1}: R$ {subtotal_item:.2f}**")
            
            itens.append({
                'produto_id': produto_id,
                'quantidade': quantidade,
                'preco_unitario': preco_unitario
            })
        
        # Calcular total
        total = sum(item['quantidade'] * item['preco_unitario'] for item in itens)
        st.subheader(f"💰 Total do Orçamento: R$ {total:.2f}")
        
        submitted = st.form_submit_button("Criar Orçamento")
        
        if submitted:
            if cliente_id and itens:
                try:
                    orcamento_id, numero_orcamento = db.inserir_orcamento(
                        cliente_id, data_validade, observacoes, itens
                    )
                    st.success(f"Orçamento criado com sucesso! Número: {numero_orcamento}")
                    
                    # Mostrar resumo
                    st.subheader("📋 Resumo do Orçamento")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Número:** {numero_orcamento}")
                        st.write(f"**Cliente:** {cliente_selecionado}")
                        st.write(f"**Data de validade:** {data_validade}")
                    
                    with col2:
                        st.write(f"**Total de itens:** {len(itens)}")
                        st.write(f"**Total:** R$ {total:.2f}")
                        st.write(f"**Status:** Pendente")
                        
                except Exception as e:
                    st.error(f"Erro ao criar orçamento: {str(e)}")
            else:
                st.error("Preencha todos os campos obrigatórios!")

# Função para visualizar orçamentos
def orcamentos():
    # Verificar permissão
    if 'user_role' in st.session_state and st.session_state.user_role != 'admin':
        st.warning("⚠️ Acesso restrito. Apenas administradores podem visualizar orçamentos.")
        st.info("Entre em contato com o administrador para solicitar acesso.")
        return
    
    st.title("📊 Orçamentos")
    
    orcamentos_df = db.buscar_orcamentos()
    
    if not orcamentos_df.empty:
        # Formatação das datas
        orcamentos_df['data_orcamento'] = pd.to_datetime(orcamentos_df['data_orcamento']).dt.strftime('%d/%m/%Y %H:%M')
        orcamentos_df['data_validade'] = pd.to_datetime(orcamentos_df['data_validade']).dt.strftime('%d/%m/%Y')
        orcamentos_df['total'] = orcamentos_df['total'].apply(lambda x: f"R$ {x:.2f}")
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox("Filtrar por status", ["Todos"] + list(orcamentos_df['status'].unique()))
        
        with col2:
            search = st.text_input("Buscar por número ou cliente")
        
        # Aplicar filtros
        filtered_df = orcamentos_df.copy()
        
        if status_filter != "Todos":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        
        if search:
            filtered_df = filtered_df[
                filtered_df['numero_orcamento'].str.contains(search, case=False) |
                filtered_df['cliente_nome'].str.contains(search, case=False)
            ]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download dos dados
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="orcamentos.csv",
            mime="text/csv"
        )
        
        # Visualizar orçamento específico
        st.subheader("🔍 Visualizar Orçamento")
        orcamento_id = st.number_input("Digite o ID do orçamento para visualizar", min_value=1, value=1)
        
        if st.button("Visualizar"):
            orcamento, itens = db.buscar_orcamento_por_id(orcamento_id)
            
            if orcamento is not None:
                st.subheader(f"Orçamento #{orcamento['numero_orcamento']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Cliente:** {orcamento['cliente_nome']}")
                    st.write(f"**Email:** {orcamento['cliente_email']}")
                    st.write(f"**Telefone:** {orcamento['cliente_telefone']}")
                
                with col2:
                    st.write(f"**Data do orçamento:** {pd.to_datetime(orcamento['data_orcamento']).strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"**Data de validade:** {pd.to_datetime(orcamento['data_validade']).strftime('%d/%m/%Y')}")
                    st.write(f"**Status:** {orcamento['status']}")
                
                if orcamento['observacoes']:
                    st.write(f"**Observações:** {orcamento['observacoes']}")
                
                st.subheader("Itens do Orçamento")
                if not itens.empty:
                    itens_display = itens[['produto_nome', 'quantidade', 'preco_unitario', 'subtotal']].copy()
                    itens_display['preco_unitario'] = itens_display['preco_unitario'].apply(lambda x: f"R$ {x:.2f}")
                    itens_display['subtotal'] = itens_display['subtotal'].apply(lambda x: f"R$ {x:.2f}")
                    st.dataframe(itens_display, use_container_width=True)
                    
                    st.subheader(f"💰 Total: R$ {orcamento['total']:.2f}")
                else:
                    st.info("Nenhum item encontrado para este orçamento.")
            else:
                st.error("Orçamento não encontrado!")
    else:
        st.info("Nenhum orçamento encontrado.")

# Função para relatórios
def relatorios():
    # Verificar permissão
    if 'user_role' in st.session_state and st.session_state.user_role != 'admin':
        st.warning("⚠️ Acesso restrito. Apenas administradores podem acessar relatórios.")
        st.info("Entre em contato com o administrador para solicitar acesso.")
        return
    
    st.title("📈 Relatórios")
    
    orcamentos_df = db.buscar_orcamentos()
    
    if not orcamentos_df.empty:
        # Converter datas
        orcamentos_df['data_orcamento'] = pd.to_datetime(orcamentos_df['data_orcamento'])
        orcamentos_df['data_validade'] = pd.to_datetime(orcamentos_df['data_validade'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Vendas por Mês")
            orcamentos_df['mes'] = orcamentos_df['data_orcamento'].dt.strftime('%Y-%m')
            vendas_por_mes = orcamentos_df.groupby('mes')['total'].sum().reset_index()
            
            fig = px.bar(vendas_por_mes, x='mes', y='total', 
                        title='Vendas por Mês', labels={'total': 'Total (R$)', 'mes': 'Mês'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Status dos Orçamentos")
            status_counts = orcamentos_df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title='Distribuição por Status')
            st.plotly_chart(fig, use_container_width=True)
        
        # Top clientes
        st.subheader("🏆 Top Clientes")
        top_clientes = orcamentos_df.groupby('cliente_nome')['total'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(x=top_clientes.values, y=top_clientes.index, orientation='h',
                    title='Top 10 Clientes por Valor Total', labels={'x': 'Total (R$)', 'y': 'Cliente'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas gerais
        st.subheader("📋 Estatísticas Gerais")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Orçamentos", len(orcamentos_df))
        
        with col2:
            st.metric("Valor Total", f"R$ {orcamentos_df['total'].sum():,.2f}")
        
        with col3:
            st.metric("Ticket Médio", f"R$ {orcamentos_df['total'].mean():,.2f}")
        
        with col4:
            st.metric("Orçamentos Pendentes", len(orcamentos_df[orcamentos_df['status'] == 'Pendente']))
        
    else:
        st.info("Nenhum orçamento encontrado para gerar relatórios.")

# Navegação principal
if pagina == "🏠 Dashboard":
    dashboard()
elif pagina == "👥 Clientes":
    clientes()
elif pagina == "📦 Produtos":
    produtos()
elif pagina == "💰 Novo Orçamento":
    novo_orcamento()
elif pagina == "📊 Orçamentos":
    orcamentos()
elif pagina == "📈 Relatórios":
    relatorios() 