import requests
import time
import os
import json

api = "https://api.github.com"
githubToken = os.getenv("GITHUB_TOKEN")

def request(url, params, headers, timeout, attempts = 5) -> requests.Response | None:
    for attempt in range(1, attempts + 1):
        try: 
            req = requests.get(
                url = url,
                params = params,
                headers = headers,
                timeout = timeout
            )

            if req.status_code == 200:
                return req
            
            if req.status_code == 404:
                return None
        except Exception as e:
            print(f'Tentativa {attempt}/{attempts} falhou: {e}')

            if attempt < attempts:
                time.sleep(attempt * 2)
    return None

def query(url, params, attempts = 5):
    req = request(
        api + url,
        params, 
        { "Authorization": f"Bearer {githubToken}" },
        None,
        attempts
    )

    return req.json() if not req == None else None

def process_versions():
    res = query("/repos/Anuken/Mindustry/releases?per_page=100", None)
    result = []

    for version in res:
        assets = []
        for asset in version['assets']:
            assets.append({
                "name": asset['name'],
                "size": asset['size'],
                "download_count": asset['download_count'],
                "download_url": asset['browser_download_url'],
                "created_at": asset['created_at'],
                "updated_at": asset['updated_at']
            })

        body = {
            "id": version['tag_name'],
            "name": version['name'],
            "prerelease": version['prerelease'],
            "body": version['body'],
            "assets": assets,
            "created_at": version['published_at'],
            "updated_at": version['updated_at']
        }
        
        result.append(body)

    return result

result = process_versions()
result = [asset for asset in result if float(asset['id'].replace('v', '')) >= 136.0]

with open(f'data/versions.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)