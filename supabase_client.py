import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Dict

# Carregar variáveis de ambiente (opcional)
try:
    load_dotenv()
except:
    pass

class SupabaseManager:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.table_name = os.getenv("FIXED_COSTS_TABLE")
        if not self.table_name:
            raise Exception("Variável de ambiente FIXED_COSTS_TABLE deve estar configurada")
        
        # Verificar se as variáveis de ambiente estão configuradas
        if not self.supabase_url or not self.supabase_key:
            raise Exception("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY devem estar configuradas")
        
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            print("✅ Conectado ao Supabase com sucesso")
        except Exception as e:
            print(f"❌ Erro ao conectar ao Supabase: {e}")
            self.client = None
    
    def get_custos_fixos(self) -> Dict[str, float]:
        """
        Busca os custos fixos da tabela fixed_costs no Supabase
        Retorna um dicionário com os custos fixos
        """
        if not self.client:
            raise Exception("Não foi possível conectar ao Supabase para buscar custos fixos")
        
        try:
            response = self.client.table(self.table_name).select("*").execute()
            
            if not response.data:
                raise Exception("Nenhum dado encontrado na tabela fixed_costs")
            
            # Converter os dados da tabela para o formato esperado
            custos_fixos = {}
            for item in response.data:
                if 'name' in item and 'amount' in item:
                    # Converter o nome para o formato esperado pelo sistema
                    nome_normalizado = self._normalizar_nome(item['name'])
                    custos_fixos[nome_normalizado] = float(item['amount'])
            
            print(f"✅ Carregados {len(custos_fixos)} custos fixos do Supabase")
            return custos_fixos
            
        except Exception as e:
            print(f"❌ Erro ao buscar custos fixos do Supabase: {e}")
            raise Exception("Não foi possível conectar ao Supabase para buscar custos fixos")
    
    def get_constants(self) -> Dict[str, float]:
        """
        Busca as constantes da tabela constants no Supabase
        Retorna um dicionário com as constantes
        """
        if not self.client:
            raise Exception("Não foi possível conectar ao Supabase para buscar constantes")
        
        try:
            response = self.client.table("constants").select("*").execute()
            
            if not response.data:
                raise Exception("Nenhum dado encontrado na tabela constants")
            
            # Converter os dados da tabela para o formato esperado
            constants = {}
            for item in response.data:
                if 'name' in item and 'value' in item:
                    constants[item['name']] = float(item['value'])
            
            print(f"✅ Carregadas {len(constants)} constantes do Supabase")
            return constants
            
        except Exception as e:
            print(f"❌ Erro ao buscar constantes do Supabase: {e}")
            raise Exception("Não foi possível conectar ao Supabase para buscar constantes")
    
    def _normalizar_nome(self, nome: str) -> str:
        """
        Normaliza os nomes da tabela para o formato esperado pelo sistema
        """
        mapeamento = {
            'Energia (média)': 'energia',
            'Água (média)': 'agua',
            'Internet': 'internet',
            'Aluguel': 'aluguel',
            'Folha (média)': 'funcionarios',
            'Jurídico': 'manutencao',
            'Marketing': 'materiais_escritorio',
            # Adicione mais mapeamentos conforme necessário
            'Tecnoponto': 'tecnoponto',
            'Alarme': 'alarme',
            'Vale-refeição': 'vale-refeição',
            'Vale-transporte (média)': 'vale-transporte_média',
            'Combustível': 'combustível',
            'Adobe': 'adobe',
            'Meli+': 'meli+',
            'Kommo': 'kommo',
            'INSS (média)': 'inss_média',
            'FGTS (média)': 'fgts_média',
            'DAS (média)': 'das_média',
            'CIM/TLF/TVS': 'cim/tlf/tvs',
            'Fronteira (média)': 'fronteira_média',
            'Contabilidade': 'contabilidade',
            'Financeiro': 'financeiro',
            'Caixas por mês': 'caixas_por_mes' # Added for completeness, though it's a quantity not a cost
        }
        
        return mapeamento.get(nome, nome.lower().replace(' ', '_').replace('(', '').replace(')', ''))

# Instância global do SupabaseManager
supabase_manager = None

def get_supabase_manager() -> SupabaseManager:
    """
    Retorna uma instância do SupabaseManager
    """
    global supabase_manager
    if supabase_manager is None:
        try:
            supabase_manager = SupabaseManager()
        except Exception as e:
            print(f"❌ Erro ao inicializar SupabaseManager: {e}")
            raise Exception(f"Não foi possível conectar ao Supabase: {e}")
    return supabase_manager 