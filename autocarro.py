import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import time
import urllib3

# Silenciar avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÕES ---
# Adicionei &categoria=3 (Hatch) na URL para já ajudar a filtrar na fonte
URL_BUSCA = "https://m.autocarro.com.br/autobusca/carros?q=etios%201.5&ano_de=2016&preco_ate=65000&cambio=1&estado=43&categoria=3&sort=1"

# Secrets
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')


def enviar_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f" [!] Sem config de Telegram. Msg seria: {msg}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")


def main():
    print("--- Iniciando Autocarro v3 (No-Sedan + Cidades) ---")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }

    try:
        response = requests.get(
            URL_BUSCA, headers=headers, timeout=30, verify=False)
    except Exception as e:
        print(f"Erro fatal de conexão: {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.content, 'html.parser')
    script_tag = soup.find('script', id='__NEXT_DATA__')

    if not script_tag:
        print("❌ ERRO: Tag __NEXT_DATA__ não encontrada.")
        sys.exit(1)

    try:
        data_json = json.loads(script_tag.string)
        page_props = data_json.get('props', {}).get('pageProps', {})

        # 1. CRIAR O MAPA DE CIDADES (ID -> NOME)
        # O JSON traz uma lista de todas as cidades do RS na estrutura de filtros
        mapa_cidades = {}
        try:
            lista_cidades = page_props['search']['filters']['data']['cidades']
            for c in lista_cidades:
                # Ex: { "id_cid": 4323002, "ds_cid": "VIAMAO", ... }
                mapa_cidades[c['id_cid']] = c['ds_cid']
            print(
                f"Mapa de cidades carregado: {len(mapa_cidades)} cidades conhecidas.")
        except KeyError:
            print(
                "Aviso: Não foi possível carregar o mapa de cidades. Os IDs serão usados.")

        # 2. BUSCAR CARROS
        offers = page_props.get('offers', {})
        lista_carros = offers.get('items', [])

        print(f"Total bruto encontrado: {len(lista_carros)}")
        enviados = 0

        for carro in lista_carros:
            # Pega versão e modelo para verificar se é Sedan
            version = carro.get('version', '').upper()
            model = carro.get('model', '').upper()
            nome_completo = f"{model} {version}"

            # --- FILTRO ANTI-SEDAN ---
            if 'SEDAN' in nome_completo:
                print(f"🚫 Ignorando Sedan: {nome_completo}")
                continue

            # --- TRADUÇÃO DA CIDADE ---
            city_id = carro.get('cityId')
            # Tenta pegar o nome no mapa, se não achar, usa o ID mesmo
            city_name = mapa_cidades.get(city_id, str(city_id))

            preco = carro.get('priceCurrency', 'R$ 0')
            year_model = carro.get('yearModel')
            link = carro.get('link')

            print(f"-> Enviando: {nome_completo} - {city_name}")

            msg = (
                f"🚗 <b>{nome_completo}</b>\n"
                f"💰 {preco} | 📅 {year_model}\n"
                f"📍 Local: {city_name}\n"
                f"🔗 <a href='{link}'>Ver Anúncio</a>"
            )
            enviar_telegram(msg)
            enviados += 1
            time.sleep(1)

        if enviados == 0:
            print("Nenhum Hatch encontrado nos filtros.")

    except Exception as e:
        print(f"❌ Erro ao processar JSON: {e}")


if __name__ == "__main__":
    main()
