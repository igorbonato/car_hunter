import requests
import json
import os
import sys
import time

URL_API = "https://www.webmotors.com.br/api/search/car?url=https:%2F%2Fwww.webmotors.com.br%2Fcarros%2Frs%3Fautocomplete%3Detios%2520%26autocompleteTerm%3DTOYOTA%2520ETIOS%26lkid%3D1705%26tipoveiculo%3Dcarros%26estadocidade%3DRio%2520Grande%2520do%2520Sul%26marca1%3DTOYOTA%26modelo1%3DETIOS%26versao1%3D1.5%2520X%2520PLUS%252016V%2520FLEX%25204P%2520MANUAL%26marca2%3DTOYOTA%26modelo2%3DETIOS%26versao2%3D1.5%2520XLS%252016V%2520FLEX%25204P%2520MANUAL%26marca3%3DTOYOTA%26modelo3%3DETIOS%26versao3%3D1.5%2520XS%252016V%2520FLEX%25204P%2520MANUAL%26page%3D1%26anode%3D2016%26cambio%3DManual%26precoate%3D65000&displayPerPage=24&actualPage=1&showMenu=true&showCount=true&showBreadCrumb=true&order=1&mediaZeroKm=true"

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')


def enviar_telegram(carro):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    preco = carro.get('Prices', 'R$ 0')
    if isinstance(preco, float) or isinstance(preco, int):
        preco = f"R$ {preco}"

    link = f"https://www.webmotors.com.br/comprar/carro/{carro['UniqueId']}"

    mensagem = (
        f"🏎️ <b>Webmotors: Etios Encontrado!</b>\n\n"
        f"🚘 <b>{carro.get('SpecificationTitle', 'Toyota Etios')}</b>\n"
        f"📅 Ano: {carro.get('YearFab')}/{carro.get('YearModel')}\n"
        f"💰 Preço: {preco}\n"
        f"📟 KM: {carro.get('KM')}\n"
        f"📍 Local: {carro.get('City', 'N/A')} - {carro.get('State', 'RS')}\n"
        f"🔗 <a href='{link}'>Ver Anúncio</a>"
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
        print(f"Erro Telegram: {e}")


def main():
    print("--- Iniciando Webmotors ---")

    headers = {
        'authority': 'www.webmotors.com.br',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'origin': 'https://www.webmotors.com.br',
        'referer': 'https://www.webmotors.com.br/carros/rs?autocomplete=etios&perfil=carros&modelo=etios',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    try:
        response = requests.get(URL_API, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"Erro Webmotors: {response.status_code}")
            # print(response.text)
            sys.exit(1)

        data = response.json()

        lista_carros = data.get('SearchResults', [])

        print(f"Encontrados: {len(lista_carros)}")

        for carro in lista_carros:
            titulo = carro.get('SpecificationTitle', '').upper()
            if 'AUTOMÁTICO' in titulo:
                continue

            print(f"-> {carro.get('UniqueId')} - {carro.get('Prices')}")
            enviar_telegram(carro)

    except Exception as e:
        print(f"Erro fatal no script: {e}")
        pass


if __name__ == "__main__":
    main()
