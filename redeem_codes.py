import os
import re
import httpx
import xml.etree.ElementTree as ET

# Configurações via Variáveis de Ambiente (GitHub Secrets)
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
    """Varre o feed RSS de busca do Reddit em busca de códigos válidos"""
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
                    if not match.isalpha() or match.isupper():
                        codigos_encontrados.add(match)
                        
    except Exception as e:
        print(f"Erro ao varrer o Reddit: {e}")
    
    return list(codigos_encontrados)

if __name__ == "__main__":
    print("Iniciando varredura de códigos do Genshin...")
    codigos = buscar_codigos_reddit()
    
    if codigos:
        # Formata a lista de códigos em bullet points para o Telegram
        lista_formatada = "\n".join([f"• `{codigo}`" for codigo in codigos])
        msg = f"🎁 *Novos Códigos do Genshin Encontrados!*\n\nAqui estão os códigos mapeados recentemente:\n\n{lista_formatada}"
        print(f"Enviando {len(codigos)} códigos para o Telegram...")
        enviar_telegram(msg)
    else:
        print("Nenhum código novo encontrado nesta execução.")
