import os
import sys
import io
import json
import requests
from bs4 import BeautifulSoup
from pdf2image import convert_from_bytes

# --- Configurações ---
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

        # Busca o botão específico da lista
        link_element = soup.find('a', class_='list-item__button')

        if not link_element:
            print("❌ Erro: Nenhum elemento 'list-item__button' encontrado.")
            return None, None

        url_pdf = link_element['href']
        title = link_element.get('title', 'Diário Oficial de Guararema')

        # Garante URL absoluta
        if not url_pdf.startswith('http'):
            url_pdf = f"https://guararema.sp.gov.br{url_pdf}"

        return url_pdf, title

    except Exception as e:
        print(f"❌ Erro ao acessar o site: {e}")
        return None, None

def send_to_telegram(pdf_url, title):
    """Converte páginas em imagens e envia álbum + PDF."""
    print(f"🚀 Iniciando envio de: {title}")

    try:
        # 1. Baixar o PDF
        pdf_response = requests.get(pdf_url, timeout=30)
        pdf_response.raise_for_status()
        pdf_bytes = pdf_response.content

        # 2. Converter páginas em imagens (Memória)
        print("📸 Convertendo PDF em imagens...")
        # Converte em JPEG. Se o PDF tiver mais de 10 páginas, corta na 10ª (limite do Telegram)
        pages = convert_from_bytes(pdf_bytes, fmt="jpeg")

        if len(pages) > 10:
            print(f"⚠️ PDF longo ({len(pages)} págs). Limitando às 10 primeiras para o álbum.")
            pages = pages[:10]

        # 3. Preparar o Álbum (MediaGroup)
        api_url_album = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMediaGroup"

        files = {}
        media_group = []

        caption_text = (
            f"🏛️ *{title}*\n\n"
            f"📖 *Visualização Rápida:*\n"
            f"Arraste para o lado para ler as páginas.\n\n"
            f"📎 O arquivo original está logo abaixo. 👇"
        )

        for i, page in enumerate(pages):
            # Salva imagem em buffer de memória
            img_byte_arr = io.BytesIO()
            page.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr.seek(0)

            # Chaves únicas para o multipart/form-data
            file_key = f'photo{i}'
            filename = f'page_{i+1}.jpg'

            files[file_key] = (filename, img_byte_arr, 'image/jpeg')

            media_item = {
                'type': 'photo',
                'media': f'attach://{file_key}'
            }

            # A legenda só vai na primeira foto
            if i == 0:
                media_item['caption'] = caption_text
                media_item['parse_mode'] = 'Markdown'

            media_group.append(media_item)

        # Envia o Álbum
        print(f"📤 Enviando álbum com {len(pages)} imagens...")
        resp_album = requests.post(api_url_album, data={'chat_id': CHANNEL_ID, 'media': json.dumps(media_group)}, files=files)

        if resp_album.status_code != 200:
            print(f"⚠️ Erro ao enviar álbum: {resp_album.text}")
            # Não retornamos False aqui para tentar enviar o PDF mesmo se o álbum falhar

        # 4. Enviar o arquivo PDF (Documento)
        print("📤 Enviando arquivo PDF...")
        api_url_doc = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        filename_pdf = f"Diario_Guararema_{title.replace(' ', '_')[:50]}.pdf" # Limita nome longo

        files_doc = {'document': (filename_pdf, pdf_bytes, 'application/pdf')}
        data_doc = {'chat_id': CHANNEL_ID}

        resp_doc = requests.post(api_url_doc, files=files_doc, data=data_doc)

        if resp_doc.status_code == 200:
            print("✅ Sucesso total!")
            return True
        else:
            print(f"❌ Erro ao enviar PDF: {resp_doc.text}")
            return False

    except Exception as e:
        print(f"❌ Erro crítico no processo: {e}")
        return False

def main():
    # 1. Checa site
    latest_url, latest_title = get_latest_diario()

    if not latest_url:
        print("Falha ao obter URL.")
        sys.exit(1)

    # 2. Checa estado local
    last_processed = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            last_processed = f.read().strip()

    print(f"🔍 Site: {latest_url}")
    print(f"🔍 Local: {last_processed}")

    if latest_url == last_processed:
        print("💤 Nada novo sob o sol.")
        return

    # 3. Envia e atualiza
    if send_to_telegram(latest_url, latest_title):
        with open(STATE_FILE, 'w') as f:
            f.write(latest_url)
        print("💾 Estado atualizado.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not CHANNEL_ID:
        print("❌ Erro: Variáveis de ambiente não configuradas.")
        sys.exit(1)
    main()
