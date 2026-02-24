import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import time
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL_BUSCA = "https://m.autocarro.com.br/autobusca/carros?q=etios%201.5&ano_de=2016&preco_ate=65000&cambio=1&estado=43&sort=1"

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

ARQUIVO_MEMORIA = "price_memory.json"


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


def carregar_memoria():
    if os.path.exists(ARQUIVO_MEMORIA):
        try:
            with open(ARQUIVO_MEMORIA, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def salvar_memoria(dados):
    with open(ARQUIVO_MEMORIA, 'w') as f:
        json.dump(dados, f, indent=4)


def limpar_preco(preco_str):
    try:
        limpo = preco_str.replace('R$', '').replace(
            '.', '').replace(',', '.').strip()
        return float(limpo)
    except:
        return 0.0


def main():
    print("--- Iniciando Autocarro (Relatório Completo) ---")

    memoria = carregar_memoria()
    nova_memoria = memoria.copy()

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

        msgs_para_enviar = []

        for carro in lista_bruta:
            version = carro.get('version', '').upper()
            model = carro.get('model', '').upper()
            nome_completo = f"{model} {version}"

            link = carro.get('link')
            car_id = str(carro.get('id', link))

            preco_visual = carro.get('priceCurrency', 'R$ 0')
            preco_float = limpar_preco(preco_visual)

            status_aviso = ""
            preco_antigo = memoria.get(car_id)

            if car_id not in memoria:
                status_aviso = "🆕 <b>NOVO ANÚNCIO!</b>"
                nova_memoria[car_id] = preco_float

            elif preco_float != preco_antigo:
                diferenca = preco_float - preco_antigo
                if diferenca < 0:
                    status_aviso = f"📉 <b>BAIXOU!</b> (Era R$ {preco_antigo:,.0f})"
                else:
                    status_aviso = f"📈 <b>SUBIU!</b> (Era R$ {preco_antigo:,.0f})"

                nova_memoria[car_id] = preco_float

            else:
                status_aviso = "⚪ Preço Mantido"

            city_id = carro.get('cityId')
            city_name = mapa_cidades.get(city_id, str(city_id))
            year_model = carro.get('yearModel')

            print(f"-> Preparando envio: {status_aviso} - {nome_completo}")

            msg = (
                f"{status_aviso}\n"
                f"🚗 <b>{nome_completo}</b>\n"
                f"💰 {preco_visual} | 📅 {year_model}\n"
                f"📍 Local: {city_name}\n"
                f"🔗 <a href='{link}'>Ver Anúncio</a>"
            )
            msgs_para_enviar.append(msg)

        print(
            f"Bruto: {len(lista_bruta)} | Para Enviar: {len(msgs_para_enviar)}")

        if len(msgs_para_enviar) > 0:
            fuso_brasil = datetime.now() - timedelta(hours=3)
            agora_formatada = fuso_brasil.strftime("%d/%m %H:%M")

            enviar_telegram(
                f"🏁 <b>Relatório Diário:</b> {agora_formatada}\n{'━'*50}")

            for m in msgs_para_enviar:
                enviar_telegram(m)
                time.sleep(1)

            salvar_memoria(nova_memoria)
            print("Memória de preços atualizada com sucesso.")
        else:
            print("Nenhum carro encontrado nos filtros.")

    except Exception as e:
        print(f"❌ Erro ao processar JSON: {e}")


if __name__ == "__main__":
    main()
