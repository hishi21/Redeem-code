import os
import re
import httpx
import asyncio
import genshin

# Configurações via Variáveis de Ambiente (GitHub Secrets)
LTUID = os.environ.get("HOYO_LTUID")
LTOKEN = os.environ.get("HOYO_LTOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def enviar_telegram(mensagem):
    """Envia uma notificação direta para o seu Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado. Pulando notificação.")
        return
    url = "https://www.reddit.com/r/Genshin_Impact/search.json?q=code&restrict_sr=1&sort=new&t=week"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        httpx.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def buscar_codigos_reddit():
    """Varre o JSON público do Reddit em busca de códigos válidos das últimas 24h"""
    print("Buscando códigos no Reddit...")
    url = "https://www.reddit.com/r/Genshin_Impact/search.json?q=code&restrict_sr=1&sort=new&t=day"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GenshinCodeBot/1.0"}
    
    codigos_encontrados = set()
    try:
        response = httpx.get(url, headers=headers, follow_redirects=True)
        data = response.json()
        
        padrao_codigo = re.compile(r'\b[A-Z0-9]{10,15}\b')

        for post in data['data']['children']:
            title = post['data']['title']
            selftext = post['data']['selftext']
            flair = post['data'].get('link_flair_text', '') or ''

            if 'code' in title.lower() or 'code' in flair.lower() or 'redeem' in title.lower():
                matches = padrao_codigo.findall(f"{title} {selftext}")
                for match in matches:
                    if not match.isalpha() or match.isupper():
                        codigos_encontrados.add(match)
                        
    except Exception as e:
        print(f"Erro ao varrer o Reddit: {e}")
    
    return list(codigos_encontrados)

async def rodar_resgate():
    if not LTUID or not LTOKEN:
        print("Erro: Cookies da HoYoLAB não encontrados nos Secrets.")
        return

    codigos = buscar_codigos_reddit()
    if not codigos:
        print("Nenhum código novo mapeado no Reddit nas últimas postagens.")
        return

    print(f"Códigos encontrados para teste: {codigos}")
    
    client = genshin.Client({"ltuid": LTUID, "ltoken": LTOKEN})
    
    for codigo in codigos:
        try:
            print(f"Tentando resgatar: {codigo}")
            await client.redeem_code(codigo, game=genshin.Game.GENSHIN)
            msg = f"✅ *Genshin Impact Code*\nCódigo `{codigo}` resgatado com sucesso via automação!"
            print(msg)
            enviar_telegram(msg)
        except genshin.errors.RedemptionException as e:
            print(f"Resultado para {codigo}: {e.msg}")
        except Exception as e:
            print(f"Erro inesperado no resgate do código {codigo}: {e}")

if __name__ == "__main__":
    # Notificação de teste do Telegram
    enviar_telegram("🤖 *Automação Ativa:* O script acordou e está varrendo o Reddit!")
    
    asyncio.run(rodar_resgate())
