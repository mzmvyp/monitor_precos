"""Monitor de Preços - Flask Professional Edition - 100% Python."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml
from flask import Flask, render_template, request, jsonify, send_file

from src.price_monitor import PriceMonitor
from src.flight_monitor import FlightMonitor

# Configuração
logging.basicConfig(level=logging.INFO)

app = Flask(__name__,
            template_folder='flask_app/templates',
            static_folder='flask_app/static')
app.config['SECRET_KEY'] = 'monitor-precos-professional-2025'

# Paths
CONFIG_PATH = Path("config/products.yaml")
HISTORY_PATH = Path("data/price_history.csv")
FLIGHT_CONFIG_PATH = Path("config/flights.yaml")
FLIGHT_HISTORY_PATH = Path("data/flight_history.csv")

# ============================================================
# HELPERS
# ============================================================

def load_config():
    """Carrega configuração YAML."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_config(config):
    """Salva configuração YAML."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def get_monitor():
    """Retorna instância do PriceMonitor."""
    return PriceMonitor(config_path=CONFIG_PATH, history_path=HISTORY_PATH)

def calculate_stats(config, history_df):
    """Calcula estatísticas gerais."""
    stats = {
        'total_products': len(config.get('items', [])),
        'active_products': sum(1 for item in config.get('items', []) if item.get('enabled', True)),
        'total_urls': sum(len(item.get('urls', [])) for item in config.get('items', [])),
        'total_checks': len(history_df) if not history_df.empty else 0,
        'total_savings': 0.0,
        'products_below_target': 0,
    }

    if not history_df.empty:
        monitor = get_monitor()
        latest_prices = history_df.sort_values('timestamp').groupby(['product_id', 'store']).tail(1)

        for _, row in latest_prices.iterrows():
            product = monitor.products.get(row['product_id'])
            if product and pd.notna(row['price']) and pd.notna(product.desired_price):
                if row['price'] <= product.desired_price:
                    savings = product.desired_price - row['price']
                    stats['total_savings'] += savings
                    stats['products_below_target'] += 1

    return stats

def get_last_update_info(history_df):
    """Retorna informações sobre última atualização."""
    if history_df.empty:
        return {
            'has_data': False,
            'message': 'Nenhum dado coletado ainda',
            'type': 'info'
        }

    last_update = history_df['timestamp'].max()
    time_since = datetime.now(timezone.utc) - last_update
    hours_since = time_since.total_seconds() / 3600

    brasilia_tz = ZoneInfo("America/Sao_Paulo")
    last_update_brasilia = last_update.astimezone(brasilia_tz)

    if hours_since > 24:
        alert_type = 'danger'
    elif hours_since > 6:
        alert_type = 'warning'
    else:
        alert_type = 'success'

    return {
        'has_data': True,
        'timestamp': last_update_brasilia.strftime('%d/%m/%Y às %H:%M'),
        'hours_since': int(hours_since),
        'type': alert_type
    }

# ============================================================
# ROTAS - PÁGINAS
# ============================================================

@app.route('/')
def index():
    """Dashboard principal."""
    config = load_config()
    monitor = get_monitor()
    history_df = monitor.load_history()

    if not history_df.empty:
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'], utc=True)

    stats = calculate_stats(config, history_df)
    update_info = get_last_update_info(history_df)

    # Produtos ativos
    active_products = [
        item for item in config.get('items', [])
        if item.get('enabled', True)
    ]

    # Últimos preços
    latest_prices = []
    if not history_df.empty:
        latest_df = history_df.sort_values('timestamp').groupby(['product_id', 'store']).tail(1)
        latest_prices = latest_df.to_dict('records')

    return render_template('dashboard.html',
                         stats=stats,
                         update_info=update_info,
                         products=active_products,
                         latest_prices=latest_prices,
                         page='dashboard')

@app.route('/gerenciamento')
def gerenciamento():
    """Página de gerenciamento de produtos."""
    config = load_config()

    return render_template('gerenciamento.html',
                         products=config.get('items', []),
                         page='gerenciamento')

@app.route('/estatisticas')
def estatisticas():
    """Página de estatísticas."""
    config = load_config()
    monitor = get_monitor()
    history_df = monitor.load_history()

    if not history_df.empty:
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'], utc=True)

    stats = calculate_stats(config, history_df)

    # Estatísticas por categoria
    by_category = {}
    for item in config.get('items', []):
        cat = item['category']
        if cat not in by_category:
            by_category[cat] = {'count': 0, 'active': 0, 'total_price': 0}
        by_category[cat]['count'] += 1
        if item.get('enabled', True):
            by_category[cat]['active'] += 1
        by_category[cat]['total_price'] += item.get('desired_price', 0)

    return render_template('estatisticas.html',
                         stats=stats,
                         by_category=by_category,
                         page='estatisticas')

@app.route('/voos')
def voos():
    """Página de monitoramento de voos."""
    flights_df = pd.DataFrame()

    if FLIGHT_HISTORY_PATH.exists():
        try:
            flight_monitor = FlightMonitor(
                config_path=FLIGHT_CONFIG_PATH,
                history_path=FLIGHT_HISTORY_PATH
            )
            flights_df = flight_monitor.get_latest_flights()
        except:
            pass

    flights = flights_df.to_dict('records') if not flights_df.empty else []

    return render_template('voos.html',
                         flights=flights,
                         page='voos')

@app.route('/sobre')
def sobre():
    """Página sobre o sistema."""
    return render_template('sobre.html', page='sobre')

# ============================================================
# ROTAS - API
# ============================================================

@app.route('/api/collect', methods=['POST'])
def api_collect():
    """Coleta preços dos produtos."""
    try:
        data = request.get_json() or {}
        product_ids = data.get('product_ids', None)

        monitor = get_monitor()
        snapshots = monitor.collect(product_ids=product_ids)

        return jsonify({
            'success': True,
            'message': f'✅ Coleta finalizada: {len(snapshots)} registros coletados!',
            'count': len(snapshots)
        })

    except RuntimeError as e:
        error_msg = str(e)
        if "ChromeDriver" in error_msg:
            return jsonify({
                'success': False,
                'error': '❌ ChromeDriver não instalado! Execute: python instalar_chromedriver_manual.py'
            }), 500
        return jsonify({'success': False, 'error': str(e)}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def api_products():
    """Lista todos os produtos."""
    config = load_config()
    return jsonify(config.get('items', []))

@app.route('/api/products/<product_id>', methods=['GET'])
def api_product_detail(product_id):
    """Detalhes de um produto."""
    config = load_config()
    product = next((item for item in config.get('items', []) if item['id'] == product_id), None)

    if not product:
        return jsonify({'error': 'Produto não encontrado'}), 404

    return jsonify(product)

@app.route('/api/products', methods=['POST'])
def api_product_add():
    """Adiciona novo produto."""
    try:
        data = request.get_json()
        config = load_config()

        # Validações
        if not data.get('id') or not data.get('name'):
            return jsonify({'error': 'ID e nome são obrigatórios'}), 400

        if any(item['id'] == data['id'] for item in config.get('items', [])):
            return jsonify({'error': f'Produto com ID {data["id"]} já existe'}), 400

        # Adicionar
        config.setdefault('items', []).append(data)
        save_config(config)

        return jsonify({'success': True, 'message': 'Produto adicionado com sucesso!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_id>', methods=['PUT'])
def api_product_update(product_id):
    """Atualiza produto existente."""
    try:
        data = request.get_json()
        config = load_config()

        for item in config.get('items', []):
            if item['id'] == product_id:
                item.update(data)
                save_config(config)
                return jsonify({'success': True, 'message': 'Produto atualizado!'})

        return jsonify({'error': 'Produto não encontrado'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_id>', methods=['DELETE'])
def api_product_delete(product_id):
    """Remove produto."""
    try:
        config = load_config()
        config['items'] = [item for item in config.get('items', []) if item['id'] != product_id]
        save_config(config)

        return jsonify({'success': True, 'message': 'Produto removido!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Retorna estatísticas gerais."""
    config = load_config()
    monitor = get_monitor()
    history_df = monitor.load_history()

    if not history_df.empty:
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'], utc=True)

    stats = calculate_stats(config, history_df)
    update_info = get_last_update_info(history_df)

    return jsonify({
        'stats': stats,
        'update_info': update_info
    })

@app.route('/api/history/<product_id>')
def api_history(product_id):
    """Retorna histórico de preços de um produto."""
    monitor = get_monitor()
    history_df = monitor.load_history()

    if history_df.empty:
        return jsonify([])

    product_history = history_df[history_df['product_id'] == product_id]
    return jsonify(product_history.to_dict('records'))

@app.route('/api/export/csv')
def api_export_csv():
    """Exporta produtos para CSV."""
    config = load_config()

    # Criar CSV
    rows = []
    for item in config.get('items', []):
        for url_data in item.get('urls', []):
            rows.append({
                'id': item['id'],
                'name': item['name'],
                'category': item['category'],
                'desired_price': item.get('desired_price', 0),
                'enabled': item.get('enabled', True),
                'store': url_data['store'],
                'url': url_data['url']
            })

    df = pd.DataFrame(rows)

    # Salvar temporariamente
    temp_file = Path('/tmp/produtos_export.csv')
    df.to_csv(temp_file, index=False)

    return send_file(temp_file, as_attachment=True, download_name='produtos.csv')

@app.route('/api/flights/collect', methods=['POST'])
def api_flights_collect():
    """Busca voos."""
    try:
        flight_monitor = FlightMonitor(
            config_path=FLIGHT_CONFIG_PATH,
            history_path=FLIGHT_HISTORY_PATH
        )
        flights = flight_monitor.collect()
        flight_monitor.close()

        return jsonify({
            'success': True,
            'message': f'✅ {len(flights)} voos encontrados!',
            'count': len(flights)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# EXECUTAR
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  Monitor de Preços - Flask Professional Edition")
    print("  100% Python - Sem Node.js!")
    print("=" * 60)
    print()
    print("  Dashboard: http://localhost:5000")
    print()
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
