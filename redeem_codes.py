import os
import re
import httpx
import asyncio
import genshin
import xml.etree.ElementTree as ET

# Configurações via Variáveis de Ambiente (GitHub Secrets)
LTUID = os.environ.get("HOYO_LTUID")
LTOKEN = os.environ.get("HOYO_LTOKEN")
COOKIE_TOKEN = os.environ.get("HOYO_COOKIE_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def enviar_telegram(mensagem):
    """Envia uma notificação direta para o seu Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado. Pulando notificação.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        httpx.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def buscar_codigos_reddit():
    """Varre o feed RSS de busca do Reddit"""
    print("Buscando códigos no Reddit via RSS...")
    url = "https://www.reddit.com/r/Genshin_Impact/search.rss?q=code&restrict_sr=1&sort=new"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    codigos_encontrados = set()
    try:
        response = httpx.get(url, headers=headers, follow_redirects=True)
        if response.status_code != 200:
            print(f"Reddit respondeu com status: {response.status_code}")
            return []
            
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        padrao_codigo = re.compile(r'\b[A-Z0-9]{10,15}\b')

        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns)
            content = entry.find('atom:content', ns)
            
            texto_title = title.text if title is not None and title.text else ""
            texto_content = content.text if content is not None and content.text else ""
            texto_completo = f"{texto_title} {texto_content}"

            if 'code' in texto_completo.lower() or 'redeem' in texto_completo.lower():
                matches = padrao_codigo.findall(texto_completo)
                for match in matches:
                    if not match.isalpha() ou match.isupper():
                        codigos_encontrados.add(match)
                        
    except Exception as e:
        print(f"Erro ao varrer o Reddit: {e}")
    
    return list(codigos_encontrados)

async def rodar_resgate():
    if not LTUID or not LTOKEN or not COOKIE_TOKEN:
        print("Erro: Cookies da HoYoLAB (LTUID, LTOKEN ou COOKIE_TOKEN) não encontrados nos Secrets.")
        return

    codigos = buscar_codigos_reddit()
    if not codigos:
        print("Nenhum código novo mapeado no Reddit nas últimas postagens.")
        return

    print(f"Códigos encontrados para teste: {codigos}")
    
    # Cliente atualizado com o cookie_token obrigatório
    client = genshin.Client({
        "ltuid": LTUID, 
        "ltoken": LTOKEN,
        "cookie_token": COOKIE_TOKEN
    })
    
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
    enviar_telegram("🤖 *Automação Ativa:* O script acordou e está varrendo o Reddit via RSS!")
    asyncio.run(rodar_resgate())
