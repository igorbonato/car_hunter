import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import time
import urllib3

# Silenciar avisos de SSL (já que usamos verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÕES ---
# URL Genérica para teste (Etios, RS). Se esta funcionar, depois você ajusta os filtros.
URL_BUSCA = "https://m.autocarro.com.br/autobusca/carros?q=etios%201.5&estado=43&sort=1"

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
    print("--- DEBUG: Iniciando Autocarro v2 ---")

    # Headers completos de um Chrome no Windows
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.google.com/'
    }

    try:
        # verify=False é essencial aqui
        response = requests.get(
            URL_BUSCA, headers=headers, timeout=30, verify=False)
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        print(f"Erro fatal de conexão: {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.content, 'html.parser')

    # 1. DEBUG: O que o robô está vendo?
    titulo = soup.title.string if soup.title else "SEM TITULO"
    print(f"Título da Página: {titulo}")

    # Se o título for suspeito (ex: 'Attention Required', 'Just a moment'), fomos bloqueados.

    # 2. Tenta pegar o JSON
    script_tag = soup.find('script', id='__NEXT_DATA__')

    if not script_tag:
        print("❌ ERRO: Tag __NEXT_DATA__ não encontrada.")
        # Printar um pedaço do HTML para entender o que veio
        print("Início do HTML recebido:")
        print(str(soup)[:500])
        sys.exit(1)

    try:
        data_json = json.loads(script_tag.string)

        # Vamos tentar navegar com segurança e printar onde falha
        props = data_json.get('props', {})
        page_props = props.get('pageProps', {})

        # Debug: Verificar se a busca retornou algo nos filtros
        search_meta = page_props.get('search', {})
        print(
            f"Filtros aplicados pelo site: {json.dumps(search_meta.get('filters', {}).get('values', {}), indent=2)}")

        offers = page_props.get('offers', {})
        lista_carros = offers.get('items', [])

        print(f"Total encontrado no JSON: {len(lista_carros)}")

        if len(lista_carros) == 0:
            print(
                "⚠️ A lista veio vazia. Verifique se a URL tem carros disponíveis manualmente.")
            enviar_telegram(
                "⚠️ O Bot rodou mas não achou carros. Verifique os logs.")

        for carro in lista_carros:
            preco = carro.get('priceCurrency', 'R$ 0')
            nome = f"{carro.get('model')} {carro.get('version')}"
            print(f"-> Achei: {nome} - {preco}")

            # Monta msg
            msg = (
                f"🚗 <b>{nome}</b>\n"
                f"💰 {preco} | 📅 {carro.get('yearModel')}\n"
                f"🔗 <a href='{carro.get('link')}'>Ver Anúncio</a>"
            )
            enviar_telegram(msg)
            time.sleep(1)  # Delay para não travar o telegram

    except Exception as e:
        print(f"❌ Erro ao processar JSON: {e}")
        # Debug do JSON
        # print(script_tag.string[:500])


if __name__ == "__main__":
    main()
