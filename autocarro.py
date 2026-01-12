import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import time
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


URL_BUSCA = "https://m.autocarro.com.br/autobusca/carros?q=etios%201.5&ano_de=2016&preco_ate=65000&cambio=1&estado=43&sort=1"

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
    print("--- Iniciando Autocarro Final (Sniper + Cidades + Separador) ---")

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

        mapa_cidades = {}
        try:
            lista_cidades = page_props['search']['filters']['data']['cidades']
            for c in lista_cidades:
                mapa_cidades[c['id_cid']] = c['ds_cid']
            print(f"Mapa de cidades carregado: {len(mapa_cidades)} cidades.")
        except KeyError:
            print("Aviso: Mapa de cidades indisponível.")

        offers = page_props.get('offers', {})
        lista_bruta = offers.get('items', [])

        carros_validos = []
        for carro in lista_bruta:
            version = carro.get('version', '').upper()
            model = carro.get('model', '').upper()
            nome_completo = f"{model} {version}"

            if 'SEDAN' in nome_completo:
                continue

            carros_validos.append(carro)

        print(
            f"Bruto: {len(lista_bruta)} | Válidos (Hatch): {len(carros_validos)}")

        if len(carros_validos) > 0:
            agora = datetime.now().strftime("%d/%m %H:%M")
            enviar_telegram(f"🏁 <b>Resultado da Busca:</b> {agora}\n{'━'*20}")

            for carro in carros_validos:
                version = carro.get('version', '').upper()
                model = carro.get('model', '').upper()
                nome_completo = f"{model} {version}"

                city_id = carro.get('cityId')
                city_name = mapa_cidades.get(city_id, str(city_id))

                preco = carro.get('priceCurrency', 'R$ 0')
                year_model = carro.get('yearModel')
                link = carro.get('link')

                print(f"-> Enviando: {nome_completo} - {preco}")

                msg = (
                    f"🚗 <b>{nome_completo}</b>\n"
                    f"💰 {preco} | 📅 {year_model}\n"
                    f"📍 Local: {city_name}\n"
                    f"🔗 <a href='{link}'>Ver Anúncio</a>"
                )
                enviar_telegram(msg)
                time.sleep(1)
        else:
            print("Nenhum carro válido encontrado nesta rodada.")

    except Exception as e:
        print(f"❌ Erro ao processar JSON: {e}")


if __name__ == "__main__":
    main()
