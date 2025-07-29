import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import streamlit as st
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

class SupabaseManager:
    def __init__(self):
        self.supabase: Client = None
        self.init_supabase()
    
    def init_supabase(self):
        """Inicializa a conexão com o Supabase"""
        try:
            if SUPABASE_URL and SUPABASE_KEY:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                # Testa a conexão
                self.supabase.table('clientes').select('id').limit(1).execute()
                print("✅ Conexão com Supabase estabelecida!")
            else:
                st.error("❌ Configurações do Supabase não encontradas!")
                st.info("📝 Crie um arquivo .env com SUPABASE_URL e SUPABASE_KEY")
        except Exception as e:
            st.error(f"❌ Erro ao conectar com Supabase: {str(e)}")
            st.info("🔧 Verifique suas configurações no arquivo .env")
    
    def inserir_cliente(self, nome, email="", telefone="", cpf_cnpj="", endereco="", pessoa="fisica"):
        """Insere um novo cliente no Supabase"""
        try:
            # Usar o tipo de pessoa fornecido ou determinar baseado no CPF/CNPJ
            inscricao = ""
            
            if cpf_cnpj:
                inscricao = cpf_cnpj
            
            # Extrair representante do endereco
            representante = ""
            if endereco:
                if "Representante:" in endereco:
                    representante = endereco.split("Representante:")[1].strip()
            
            data = {
                'nome': nome,
                'inscricao': inscricao,
                'contato': telefone,
                'representante': representante,
                'email': email,
                'pessoa': pessoa
            }
            
            result = self.supabase.table('clientes').insert(data).execute()
            cliente_id = result.data[0]['id']
            return cliente_id
        except Exception as e:
            st.error(f"❌ Erro ao inserir cliente: {str(e)}")
            return None
    
    def buscar_clientes(self):
        """Retorna todos os clientes do Supabase"""
        try:
            result = self.supabase.table('clientes').select('*').order('nome').execute()
            df = pd.DataFrame(result.data)
            
            # Adicionar colunas para compatibilidade com o código existente
            if not df.empty:
                # Usar inscricao como cpf_cnpj
                df['cpf_cnpj'] = df['inscricao'].fillna('')
                
                # Renomear contato para telefone
                df['telefone'] = df['contato']
                
                # Garantir que a coluna pessoa existe
                if 'pessoa' not in df.columns:
                    df['pessoa'] = 'fisica'  # valor padrão
                
                # Garantir que a coluna representante existe
                if 'representante' not in df.columns:
                    df['representante'] = ''
                
                # Garantir que a coluna id existe
                if 'id' not in df.columns:
                    df['id'] = range(1, len(df) + 1)
                
                # Adicionar data_cadastro se não existir
                if 'created_at' in df.columns:
                    df['data_cadastro'] = df['created_at']
                else:
                    df['data_cadastro'] = datetime.now().isoformat()
            
            return df
        except Exception as e:
            st.error(f"❌ Erro ao buscar clientes: {str(e)}")
            return pd.DataFrame()
    
    def inserir_produto(self, nome, descricao="", preco_unitario=0, categoria=""):
        """Insere um novo produto no Supabase"""
        try:
            data = {
                'nome': nome,
                'descricao': descricao,
                'preco_unitario': preco_unitario,
                'categoria': categoria,
                'data_cadastro': datetime.now().isoformat()
            }
            
            result = self.supabase.table('produtos').insert(data).execute()
            produto_id = result.data[0]['id']
            return produto_id
        except Exception as e:
            st.error(f"❌ Erro ao inserir produto: {str(e)}")
            return None
    
    def buscar_produtos(self):
        """Retorna todos os produtos do Supabase"""
        try:
            result = self.supabase.table('produtos').select('*').order('nome').execute()
            df = pd.DataFrame(result.data)
            return df
        except Exception as e:
            st.error(f"❌ Erro ao buscar produtos: {str(e)}")
            return pd.DataFrame()
    
    def gerar_numero_orcamento(self):
        """Gera um número único para o orçamento"""
        try:
            # Busca o último número de orçamento
            result = self.supabase.table('orcamentos').select('numero_orcamento').execute()
            
            if not result.data:
                numero = 1
            else:
                # Extrai o número do último orçamento
                ultimo_numero = result.data[-1]['numero_orcamento']
                # Formato: ORC-YYYYMMDD-001
                try:
                    numero_str = ultimo_numero.split('-')[-1]
                    numero = int(numero_str) + 1
                except:
                    numero = 1
            
            # Formato: ORC-YYYYMMDD-001
            data_atual = datetime.now().strftime("%Y%m%d")
            return f"ORC-{data_atual}-{numero:03d}"
        except Exception as e:
            st.error(f"❌ Erro ao gerar número do orçamento: {str(e)}")
            return f"ORC-{datetime.now().strftime('%Y%m%d')}-001"
    
    def inserir_orcamento(self, cliente_id, data_validade, observacoes="", itens=None):
        """Insere um novo orçamento no Supabase"""
        try:
            numero_orcamento = self.gerar_numero_orcamento()
            
            # Insere o orçamento
            orcamento_data = {
                'numero_orcamento': numero_orcamento,
                'cliente_id': cliente_id,
                'data_validade': data_validade.isoformat(),
                'observacoes': observacoes,
                'status': 'Pendente',
                'subtotal': 0,
                'desconto': 0,
                'total': 0,
                'data_orcamento': datetime.now().isoformat()
            }
            
            result = self.supabase.table('orcamentos').insert(orcamento_data).execute()
            orcamento_id = result.data[0]['id']
            
            # Insere os itens do orçamento
            if itens:
                subtotal = 0
                for item in itens:
                    item_subtotal = item['quantidade'] * item['preco_unitario']
                    subtotal += item_subtotal
                    
                    item_data = {
                        'orcamento_id': orcamento_id,
                        'produto_id': item['produto_id'],
                        'quantidade': item['quantidade'],
                        'preco_unitario': item['preco_unitario'],
                        'subtotal': item_subtotal
                    }
                    
                    self.supabase.table('itens_orcamento').insert(item_data).execute()
                
                # Atualiza o total do orçamento
                self.supabase.table('orcamentos').update({
                    'subtotal': subtotal,
                    'total': subtotal
                }).eq('id', orcamento_id).execute()
            
            return orcamento_id, numero_orcamento
        except Exception as e:
            st.error(f"❌ Erro ao inserir orçamento: {str(e)}")
            return None, None
    
    def buscar_orcamentos(self):
        """Retorna todos os orçamentos com informações do cliente"""
        try:
            # Query complexa para buscar orçamentos com dados do cliente
            result = self.supabase.table('orcamentos').select('''
                *,
                clientes!inner(nome, email)
            ''').order('data_orcamento', desc=True).execute()
            
            # Processa os dados para o formato esperado
            orcamentos = []
            for orcamento in result.data:
                orcamento['cliente_nome'] = orcamento['clientes']['nome']
                orcamento['cliente_email'] = orcamento['clientes']['email']
                del orcamento['clientes']
                orcamentos.append(orcamento)
            
            df = pd.DataFrame(orcamentos)
            return df
        except Exception as e:
            st.error(f"❌ Erro ao buscar orçamentos: {str(e)}")
            return pd.DataFrame()
    
    def buscar_orcamento_por_id(self, orcamento_id):
        """Retorna um orçamento específico com seus itens"""
        try:
            # Busca o orçamento com dados do cliente
            result = self.supabase.table('orcamentos').select('''
                *,
                clientes!inner(nome, email, telefone)
            ''').eq('id', orcamento_id).execute()
            
            if not result.data:
                return None, pd.DataFrame()
            
            orcamento = result.data[0]
            orcamento['cliente_nome'] = orcamento['clientes']['nome']
            orcamento['cliente_email'] = orcamento['clientes']['email']
            orcamento['cliente_telefone'] = orcamento['clientes']['telefone']
            del orcamento['clientes']
            
            # Busca os itens do orçamento
            itens_result = self.supabase.table('itens_orcamento').select('''
                *,
                produtos!inner(nome, descricao)
            ''').eq('orcamento_id', orcamento_id).execute()
            
            # Processa os itens
            itens = []
            for item in itens_result.data:
                item['produto_nome'] = item['produtos']['nome']
                item['produto_descricao'] = item['produtos']['descricao']
                del item['produtos']
                itens.append(item)
            
            itens_df = pd.DataFrame(itens)
            
            return orcamento, itens_df
        except Exception as e:
            st.error(f"❌ Erro ao buscar orçamento: {str(e)}")
            return None, pd.DataFrame()
    
    def autenticar_usuario(self, username, password):
        """Autentica um usuário usando Supabase Auth"""
        try:
            # Em produção, você deve usar o Supabase Auth
            # Por enquanto, vamos usar um sistema simples
            valid_users = {
                "bruno": "28187419",
                "melissa": "130188491",
                "julia": "5912849123"
            }
            
            if username in valid_users and valid_users[username] == password:
                # Definir perfil baseado no username
                if username in ['bruno', 'melissa']:
                    role = 'admin'
                elif username == 'julia':
                    role = 'atendimento'  # Perfil de atendimento para Julia
                else:
                    role = 'user'
                
                return {
                    'success': True,
                    'user': {
                        'email': username,
                        'role': role
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Credenciais inválidas'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def registrar_usuario(self, email, password, nome):
        """Registra um novo usuário"""
        try:
            # Em produção, você deve usar o Supabase Auth
            st.info("📝 Registro de usuários deve ser implementado com Supabase Auth")
            return False
        except Exception as e:
            st.error(f"❌ Erro ao registrar usuário: {str(e)}")
            return False 