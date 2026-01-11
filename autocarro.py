import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import time
import urllib3

URL_BUSCA = "https://m.autocarro.com.br/autobusca/carros?q=etios%201.5&ano_de=2017&preco_ate=65000&cambio=1&estado=43&sort=1"

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def enviar_telegram(carro):
    """Envia a mensagem formatada para o bot."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(" [!] Erro: Token ou Chat ID do Telegram não configurados.")
        return

    mensagem = (
        f"🚘 <b>{carro['model']} {carro['version']}</b>\n"
        f"📅 Ano: {carro['yearModel']}\n"
        f"💰 Preço: R$ {carro['priceCurrency']}\n"
        f"🎨 Cor: {carro.get('color', 'N/A')}\n"
        f"📍 Local: {carro.get('cityId', 'RS')}\n"
        f"🔗 <a href='{carro['link']}'>Ver Anúncio</a>"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': mensagem,
        'parse_mode': 'HTML'
    }

    try:
        requests.post(url, data=payload)
        time.sleep(1)
    except Exception as e:
        print(f"Erro ao enviar telegram: {e}")


def main():
    print("--- Iniciando Busca Completa (Sem Filtros) ---")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(
            URL_BUSCA, headers=headers, timeout=30, verify=False)
    except Exception as e:
        print(f"Erro de conexão: {e}")
        sys.exit(1)

    if response.status_code != 200:
        print(f"Erro ao acessar site: {response.status_code}")
        sys.exit(1)

    soup = BeautifulSoup(response.content, 'html.parser')
    script_tag = soup.find('script', id='__NEXT_DATA__')

    if not script_tag:
        print("Erro: Estrutura do site mudou (tag __NEXT_DATA__ não encontrada).")
        sys.exit(1)

    data_json = json.loads(script_tag.string)

    try:
        lista_carros = data_json['props']['pageProps']['offers']['items']
    except KeyError:
        print("Nenhum carro encontrado ou estrutura do JSON mudou.")
        lista_carros = []

    print(f"Encontrados {len(lista_carros)} carros. Enviando todos...")

    if not lista_carros:
        print("Lista vazia.")

    for carro in lista_carros:
        print(f"-> Enviando: {carro['version']} - {carro['priceCurrency']}")
        enviar_telegram(carro)

    print("Finalizado.")


if __name__ == "__main__":
    main()
