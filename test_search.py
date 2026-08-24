from duckduckgo_search import DDGS
import httpx

def search_and_download():
    query = "WEG W22 motor elétrico manual filetype:pdf"
    print(f"Pesquisando: {query}")
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    
    for r in results:
        url = r.get("href")
        print(f"Encontrou: {url}")
        
        print("Tentando baixar...")
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=10.0)
            if resp.status_code == 200 and b"%PDF" in resp.content[:10]:
                print(f"Sucesso! Baixou PDF com {len(resp.content)} bytes.")
                return True
            else:
                print(f"Erro: status {resp.status_code}, n\u00e3o parece PDF")
        except Exception as e:
            print(f"Erro ao baixar: {e}")
    print("Nenhum PDF encontrado ou acess\u00edvel.")
    return False

if __name__ == "__main__":
    search_and_download()
