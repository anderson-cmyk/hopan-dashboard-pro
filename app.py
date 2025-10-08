"""
HO Pan Dashboard - Aplicação Principal com Autenticação
Sistema profissional de dashboard com login seguro e integração GCP
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
import pandas as pd
import json
import requests
import os
from datetime import datetime, timedelta
import subprocess
import tempfile
import hashlib
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# Configurações do GitHub
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'anderson-cmyk/hopan-dashboard')
GITHUB_USER = os.environ.get('GITHUB_USER', 'anderson-cmyk')

# Configurações de Usuários (em produção, usar banco de dados)
USERS = {
    'admin': {
        'password': os.environ.get('ADMIN_PASSWORD_HASH', generate_password_hash('ChangeMeInProduction!')),
        'name': 'Administrador',
        'role': 'admin'
    }
}

# Adicionar usuários adicionais do ambiente
additional_users = os.environ.get('ADDITIONAL_USERS', '')
if additional_users:
    try:
        users_data = json.loads(additional_users)
        USERS.update(users_data)
    except:
        pass


def login_required(f):
    """Decorator para proteger rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator para proteger rotas que requerem privilégios de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Redireciona para login ou dashboard"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = USERS.get(username)
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user'] = username
            session['name'] = user['name']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Usuário ou senha inválidos')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html', 
                         user_name=session.get('name'),
                         user_role=session.get('role'))


@app.route('/api/data')
@login_required
def get_data():
    """API para obter dados do dashboard"""
    try:
        # Buscar dados do GitHub ou cache local
        data_file = '/tmp/dashboard_data.json'
        
        # Se o arquivo não existe ou está desatualizado, buscar do GitHub
        if not os.path.exists(data_file) or \
           (datetime.now() - datetime.fromtimestamp(os.path.getmtime(data_file))).seconds > 300:
            download_from_github(data_file)
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def download_from_github(output_file):
    """Baixa o arquivo de dados do GitHub"""
    try:
        url = f'https://raw.githubusercontent.com/{GITHUB_REPO}/main/dashboard_data.json'
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return True
    except Exception as e:
        raise Exception(f"Erro ao baixar dados do GitHub: {str(e)}")


def processar_arquivo(url_arquivo):
    """Baixa e processa o arquivo Excel"""
    try:
        response = requests.get(url_arquivo, timeout=120)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        df = pd.read_excel(tmp_path)
        os.unlink(tmp_path)
        
        return df
    except Exception as e:
        raise Exception(f"Erro ao processar arquivo: {str(e)}")


def processar_dados(df):
    """Processa e transforma os dados"""
    try:
        # Padronizar coluna de atraso
        if 'NDIAS_CON' in df.columns:
            df = df.rename(columns={'NDIAS_CON': 'ATRASO'})
        
        # Remover colunas desnecessárias
        colunas_remover = ['TxAM', 'VlrRetILA', 'DtPgtoParc', 'ComissionadoOrigem', 
                           'PMTsAgregCarteira', 'Comissao', 'QtdParc', 'TipoComiss', 
                           'FormaLib', 'SitPgtoR', 'VlrLiqLiberadoOper', 'VlrBruto',
                           'Param', 'Rateio', 'DtAgenda', 'DtFech', 'DtCadastro']
        
        for col in colunas_remover:
            if col in df.columns:
                df = df.drop(columns=[col])
        
        # Renomear colunas
        df = df.rename(columns={
            'Prop': 'Proposta',
            'VlBrutoOper': 'ValorPago',
            'ValorComiss': 'ValorComissao',
            'ATRASO': 'Atraso'
        })
        
        # Converter datas
        df['Data_Base'] = pd.to_datetime(df['Data_Base'], errors='coerce')
        df['DataVcto'] = pd.to_datetime(df['DataVcto'], errors='coerce')
        
        # Criar coluna MesAno
        df['MesAno'] = df['Data_Base'].dt.strftime('%Y-%m')
        
        # Calcular % Comissão
        df['PercComissao'] = (df['ValorComissao'] / df['ValorPago']) * 100
        
        # Criar FaixaAtraso
        def get_faixa_atraso(atraso):
            if pd.isna(atraso):
                atraso = 0
            atraso = float(atraso)
            if atraso < 0:
                atraso = 0
            
            if atraso <= 20:
                return '0-20 dias'
            elif atraso <= 30:
                return '21-30 dias'
            elif atraso <= 60:
                return '31-60 dias'
            elif atraso <= 90:
                return '61-90 dias'
            elif atraso <= 180:
                return '91-180 dias'
            elif atraso <= 360:
                return '181-360 dias'
            else:
                return 'Maior que 360 dias'
        
        df['FaixaAtraso'] = df['Atraso'].apply(get_faixa_atraso)
        
        # Criar FaixaValor
        def get_faixa_valor(valor):
            if valor <= 1000:
                return '1. Até R$ 1.000'
            elif valor <= 1500:
                return '2. R$ 1.001 a R$ 1.500'
            elif valor <= 2000:
                return '3. R$ 1.501 a R$ 2.000'
            elif valor <= 3000:
                return '4. R$ 2.001 a R$ 3.000'
            elif valor <= 5000:
                return '5. R$ 3.001 a R$ 5.000'
            elif valor <= 10000:
                return '6. R$ 5.001 a R$ 10.000'
            else:
                return '7. Maior que R$ 10.000'
        
        df['FaixaValor'] = df['ValorPago'].apply(get_faixa_valor)
        
        # Preencher valores nulos
        df['Atraso'] = df['Atraso'].fillna(0)
        
        # Selecionar colunas finais
        colunas_finais = ['Proposta', 'Cliente', 'Cpf', 'Data_Base', 'DataVcto', 
                          'ValorPago', 'ValorComissao', 'BaseCalculo', 'Atraso',
                          'PercComissao', 'FaixaAtraso', 'FaixaValor', 'MesAno', 'DtPgtoCmss']
        
        df_final = df[colunas_finais].copy()
        
        # Remover registros inválidos
        df_final = df_final.dropna(subset=['ValorPago', 'ValorComissao'])
        df_final = df_final[df_final['ValorPago'] > 0]
        
        return df_final
    except Exception as e:
        raise Exception(f"Erro ao processar dados: {str(e)}")


def gerar_json(df):
    """Gera JSON para o dashboard"""
    try:
        dados_json = df.to_dict('records')
        
        for registro in dados_json:
            for campo in ['Data_Base', 'DataVcto', 'DtPgtoCmss']:
                if campo in registro and pd.notna(registro[campo]):
                    registro[campo] = str(registro[campo])
        
        metadados = {
            'total_registros': len(df),
            'meses_disponiveis': sorted(df['MesAno'].unique().tolist()),
            'campos_numericos': ['ValorPago', 'ValorComissao', 'BaseCalculo', 'PercComissao', 'Atraso'],
            'data_atualizacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        analise_faixas = {}
        for faixa in ['0-20 dias', '21-30 dias', '31-60 dias', '61-90 dias', 
                      '91-180 dias', '181-360 dias', 'Maior que 360 dias']:
            dados_faixa = df[df['FaixaAtraso'] == faixa]
            analise_faixas[faixa] = {
                'operacoes': len(dados_faixa),
                'valor_pago': float(dados_faixa['ValorPago'].sum()),
                'valor_comissao': float(dados_faixa['ValorComissao'].sum()),
                'perc_comissao': float((dados_faixa['ValorComissao'].sum() / dados_faixa['ValorPago'].sum() * 100) if dados_faixa['ValorPago'].sum() > 0 else 0)
            }
        
        dashboard_data = {
            'metadados': metadados,
            'dados_completos': dados_json,
            'analise_faixas': analise_faixas
        }
        
        return dashboard_data
    except Exception as e:
        raise Exception(f"Erro ao gerar JSON: {str(e)}")


def atualizar_github(json_data):
    """Atualiza o arquivo no GitHub"""
    try:
        subprocess.run(['git', 'config', '--global', 'user.email', 'bot@cobhub.com'], check=True)
        subprocess.run(['git', 'config', '--global', 'user.name', 'CobHub Bot'], check=True)
        
        repo_dir = '/tmp/hopan-dashboard'
        if os.path.exists(repo_dir):
            subprocess.run(['rm', '-rf', repo_dir], check=True)
        
        clone_url = f'https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git'
        subprocess.run(['git', 'clone', clone_url, repo_dir], check=True)
        
        json_path = os.path.join(repo_dir, 'dashboard_data.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        os.chdir(repo_dir)
        subprocess.run(['git', 'add', 'dashboard_data.json'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Atualização automática via CobHub Dashboard'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        
        return True
    except Exception as e:
        raise Exception(f"Erro ao atualizar GitHub: {str(e)}")


@app.route('/api/update', methods=['POST'])
@admin_required
def update_data():
    """API para atualizar dados (apenas admin)"""
    try:
        if not request.json or 'url' not in request.json:
            return jsonify({'error': 'URL do arquivo não fornecida'}), 400
        
        url_arquivo = request.json['url']
        
        df = processar_arquivo(url_arquivo)
        df_processado = processar_dados(df)
        json_data = gerar_json(df_processado)
        atualizar_github(json_data)
        
        # Atualizar cache local
        with open('/tmp/dashboard_data.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Dashboard atualizado com sucesso',
            'registros': len(df_processado),
            'meses': json_data['metadados']['meses_disponiveis'],
            'updated_by': session.get('name')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check para Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'CobHub - HO Pan Dashboard',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
