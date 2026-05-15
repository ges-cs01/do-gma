# do-gma

Bot em Python para monitorar o Diário Oficial de Guararema e publicar automaticamente no Telegram.

## O que o projeto faz
- Acessa a página oficial do Diário Oficial de Guararema
- Identifica o PDF mais recente
- Converte as páginas em imagens (até 10 páginas para álbum)
- Publica no Telegram um álbum com pré-visualização e o PDF completo
- Salva o último link processado em `last_processed.txt`

## Requisitos
- Python 3.10+
- Poppler (`poppler-utils`) para conversão de PDF em imagem

## Instalação local
1. Instale o Poppler:
   - Ubuntu/Debian:
     ```bash
     sudo apt-get update
     sudo apt-get install -y poppler-utils
     ```
2. Instale dependências Python:
   ```bash
   pip install -r requirements.txt
   ```

## Configuração
Defina as variáveis de ambiente:

- `TELEGRAM_TOKEN`: token do bot Telegram
- `CHANNEL_ID`: ID do canal/grupo destino

Exemplo:

```bash
export TELEGRAM_TOKEN="seu_token"
export CHANNEL_ID="seu_canal"
```

## Execução
```bash
python main.py
```

## Automação no GitHub Actions
O workflow `.github/workflows/diario_bot.yml` agenda execuções em dias úteis e também permite disparo manual (`workflow_dispatch`).

## Estrutura principal
- `main.py`: lógica de scraping, conversão e envio ao Telegram
- `requirements.txt`: dependências Python
- `last_processed.txt`: controle do último diário processado
