import os
import sys
import requests
from bs4 import BeautifulSoup

# Configurações
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
STATE_FILE = 'last_processed.txt'
URL_ALVO = "https://guararema.sp.gov.br/diariooficial/"

def get_latest_diario():
    """Faz o scrape e retorna a URL e o Título do último diário."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(URL_ALVO, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Seletor específico baseado no HTML que você forneceu
        # Pega o primeiro botão da lista (assumindo ordem cronológica decrescente no site)
        link_element = soup.find('a', class_='list-item__button')

        if not link_element:
            print("❌ Erro: Nenhum elemento 'list-item__button' encontrado.")
            return None, None

        url_pdf = link_element['href']
        title = link_element.get('title', 'Diário Oficial de Guararema')

        # Garante que a URL seja absoluta
        if not url_pdf.startswith('http'):
            # Nota: O site parece usar ecrie.com.br, mas se for relativo, concatenamos
            url_pdf = f"https://guararema.sp.gov.br{url_pdf}"

        return url_pdf, title

    except Exception as e:
        print(f"❌ Erro ao acessar o site: {e}")
        return None, None

def send_to_telegram(pdf_url, title):
    """Baixa o PDF e envia para o canal."""
    print(f"📤 Enviando: {title}...")

    try:
        # Baixa o binário do PDF
        pdf_response = requests.get(pdf_url, timeout=30)
        pdf_response.raise_for_status()

        # Nome do arquivo para aparecer no download do usuário
        filename = f"Diario_Guararema_{title.replace(' ', '_')}.pdf"

        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"

        caption_text = (
            f"🏛️ *{title}*\n\n"
            f"Novo diário oficial disponível para download.\n"
            f"[Fonte Original]({pdf_url})"
        )

        files = {'document': (filename, pdf_response.content, 'application/pdf')}
        data = {
            'chat_id': CHANNEL_ID,
            'caption': caption_text,
            'parse_mode': 'Markdown'
        }

        resp = requests.post(api_url, files=files, data=data)

        if resp.status_code == 200:
            print("✅ Enviado com sucesso!")
            return True
        else:
            print(f"⚠️ Erro na API Telegram: {resp.text}")
            return False

    except Exception as e:
        print(f"❌ Erro no envio: {e}")
        return False

def main():
    # 1. Obter dados do site
    latest_url, latest_title = get_latest_diario()

    if not latest_url:
        sys.exit(1) # Sai com erro para o GitHub Actions registrar

    # 2. Ler estado anterior
    last_processed = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            last_processed = f.read().strip()

    print(f"🔍 Último processado: {last_processed}")
    print(f"🔍 Encontrado no site: {latest_url}")

    # 3. Comparar
    if latest_url == last_processed:
        print("zzz Nenhuma novidade. Encerrando.")
        return

    # 4. Enviar se for novo
    success = send_to_telegram(latest_url, latest_title)

    # 5. Atualizar estado
    if success:
        with open(STATE_FILE, 'w') as f:
            f.write(latest_url)
        print("💾 Estado atualizado.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not CHANNEL_ID:
        print("❌ Erro: Variáveis de ambiente TELEGRAM_TOKEN ou CHANNEL_ID não definidas.")
        sys.exit(1)
    main()
