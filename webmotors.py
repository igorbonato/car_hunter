from curl_cffi import requests
import os
import sys
import time
from datetime import datetime, timedelta

URL_API = "https://www.webmotors.com.br/api/search/car?url=https:%2F%2Fwww.webmotors.com.br%2Fcarros%2Frs%3Fautocomplete%3Detios%26autocompleteTerm%3DTOYOTA%2520ETIOS%26lkid%3D1705%26tipoveiculo%3Dcarros%26estadocidade%3DRio%2520Grande%2520do%2520Sul%26marca1%3DTOYOTA%26modelo1%3DETIOS%26versao1%3D1.5%2520X%2520PLUS%252016V%2520FLEX%25204P%2520MANUAL%26marca2%3DTOYOTA%26modelo2%3DETIOS%26versao2%3D1.5%2520XLS%252016V%2520FLEX%25204P%2520MANUAL%26marca3%3DTOYOTA%26modelo3%3DETIOS%26versao3%3D1.5%2520XS%252016V%2520FLEX%25204P%2520MANUAL%26page%3D1%26anode%3D2016%26cambio%3DManual%26precoate%3D65000&displayPerPage=24&actualPage=1&showMenu=true&showCount=true&showBreadCrumb=true&order=1&mediaZeroKm=true"

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')


def enviar_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f" [!] Sem config de Telegram. Msg seria: {msg}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}
    try:
        import requests as req_normal
        req_normal.post(url, data=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")


def main():
    print("--- Iniciando Webmotors v3 (CURL Impersonate) ---")

    headers = {
        'authority': 'www.webmotors.com.br',
        'accept': 'application/json, text/plain, */*',
        'referer': 'https://www.webmotors.com.br/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(URL_API, headers=headers,
                                timeout=30, impersonate="chrome120")
    except Exception as e:
        print(f"Erro fatal de conexão: {e}")
        sys.exit(1)

    if response.status_code != 200:
        print(f"Erro Webmotors: {response.status_code}")
        sys.exit(1)

    try:
        data = response.json()
        lista_carros = data.get('SearchResults', [])

        carros_validos = []
        for carro in lista_carros:
            spec = carro.get('Specification', {})
            titulo = spec.get('Title', '').upper()
            body_type = spec.get('BodyType', '').upper()

            if 'SEDAN' in titulo or 'SEDAN' in body_type:
                continue
            carros_validos.append(carro)

        print(f"Bruto: {len(lista_carros)} | Válidos: {len(carros_validos)}")

        if len(carros_validos) > 0:
            fuso_brasil = datetime.now() - timedelta(hours=3)
            agora_formatada = fuso_brasil.strftime("%d/%m %H:%M")
            enviar_telegram(
                f"🏁 <b>Webmotors Busca:</b> {agora_formatada}\n\n{'━'*30}\n")

            for carro in carros_validos:
                spec = carro.get('Specification', {})
                unique_id = carro.get('UniqueId')
                nome_completo = spec.get('Title', 'Toyota Etios')
                ano = f"{spec.get('YearFabrication', '')}/{int(spec.get('YearModel', 0))}"
                km = int(spec.get('Odometer', 0))

                prices = carro.get('Prices', {})
                preco_val = prices.get('Price', 0)
                preco_str = f"R$ {preco_val:,.2f}".replace(
                    ',', 'X').replace('.', ',').replace('X', '.')

                seller = carro.get('Seller', {})
                cidade = f"{seller.get('City', 'RS')} - {seller.get('State', 'RS')}"
                link = f"https://www.webmotors.com.br/comprar/carro/{unique_id}"

                print(f"-> Enviando: {nome_completo} - {preco_str}")

                msg = (
                    f"🏎️ <b>{nome_completo}</b>\n"
                    f"💰 {preco_str} | 📅 {ano}\n"
                    f"📟 {km} km\n"
                    f"📍 Local: {cidade}\n"
                    f"🔗 <a href='{link}'>Ver Anúncio</a>"
                )
                enviar_telegram(msg)
                time.sleep(1)
        else:
            print("Nenhum carro válido encontrado.")

    except Exception as e:
        print(f"Erro ao processar JSON: {e}")


if __name__ == "__main__":
    main()
