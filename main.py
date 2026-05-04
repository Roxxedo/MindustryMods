import requests
import time
import hjson
import math
import asyncio
import json
import shutil
import os

api = "https://api.github.com"
perPage = 100
javaLangs = ("Java", "Kotlin", "Groovy", "Scala")
blacklist = ("Snow-of-Spirit-Fox-Mori/old-mod", "fox1va-the-fox/schems", "TheSaus/Cumdustry", "Anuken/ExampleMod", "Anuken/ExampleJavaMod", "Anuken/ExampleKotlinMod", "Mesokrix/Vanilla-Upgraded", "RebornTrack970/Multiplayernt", "RebornTrack970/Multiplayerntnt", "EsqueletoBrOficial/meu-mod", "RebornTrack970/Destroyer", "RebornTrack970/Mindustrynt", "NemesisTheory/killer", "TheDogOfChaos/reset-UUID-mindustry", "OBSIDAN55/UUID_replacer", "timofeyfilkin/uuid-changer")
nameBlacklist = tuple(map(str.lower, ("TheEE145", "o7", "pixaxeofpixie", "Iron-Miner", "EasyPlaySu", "guiYMOUR", "mishakorzik", "N3M1X10", "EvilMan12317")))
topic = "mindustry-mod"
lastPushDate = "2023-11-01"
iconSize = 64

githubToken = os.getenv("GITHUB_TOKEN")

sem = asyncio.Semaphore(25)

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

def tryList(queries, attempts = 5):
    for query in queries:
        req = request(
            f'https://raw.githubusercontent.com/{query}',
            None,
            None,
            10000,
            attempts
        )

        if not req == None:
            return req.text
    return None

def tryImage(queries, attempts = 5):
    for query in queries:
        req = request(
            f'https://raw.githubusercontent.com/{query}',
            None,
            None,
            10000,
            attempts
        )

        if not req == None:
            return req.content
    return None

def parse_hjson(meta):
    if meta == None:
        return None
    
    try:
        return hjson.loads(meta, strict = False)
    except Exception:
        return None

def reset_icons():
    shutil.rmtree('data/icons', ignore_errors=True)
    os.makedirs('data/icons', exist_ok=True)

def process_image(repo, branch):
    icon = tryImage([
        f'{repo}/{branch}/icon.png',
        f'{repo}/{branch}/assets/icon.png'
    ])

    if not icon == None:
        with open(f'data/icons/{repo.replace('/', '_')}', 'wb') as f:
            f.write(icon)

def process_mod(mod, page, index, res):
    try:
        print(f"[{int(((page - 1) * perPage + index) / res['total_count'] * 100)}%] [{mod['full_name']}] querying...")

        meta = tryList([
            f'{mod['full_name']}/{mod['default_branch']}/mod.json',
            f'{mod['full_name']}/{mod['default_branch']}/mod.hjson',
            f'{mod['full_name']}/{mod['default_branch']}/assets/mod.json',
            f'{mod['full_name']}/{mod['default_branch']}/assets/mod.hjson'
        ])
        meta = parse_hjson(meta)
    
        if meta == None or meta.get('hideBrowser', False) or not float(meta.get('minGameVersion', 0)) >= 136.0:
            print(f'[{mod['full_name']}] skipping mod')
            return None
        
        process_image(mod['full_name'], mod['default_branch'])

        readme = tryList([
            f'{mod['full_name']}/{mod['default_branch']}/README.md',
            f'{mod['full_name']}/{mod['default_branch']}/readme.md',
            f'{mod['full_name']}/{mod['default_branch']}/README'
        ])
    
        releases = query(f'/repos/{mod['full_name']}/releases?per_page=100', None)
        downloads = sum(
            release['assets'][0].get('download_count', 0)
            for release in releases
            if release.get('assets')
        )
    
        body = {
            "id": mod['name'].lower(),
            "name": mod['name'],
            "repo": mod['full_name'],
            "author": mod['owner']['login'],
            "stars": mod['stargazers_count'],
            "min_game_version": meta['minGameVersion'],
            "has_scripts": mod['language'] == "JavaScript",
            "has_java": meta.get('java', False) or mod['language'] in javaLangs,
            "description": meta.get('description', ""),
            "body": readme,
            "downloads": downloads,
            "created_at": mod['created_at'],
            "updated_at": mod['pushed_at']
        }
    
        if meta.get('iosCompatible', False): body.update({ 'iosCompatible': True })
        if meta.get('legacyCompatible', False): body.update({ 'legacyCompatible': True })
    
        return body
    except Exception as e:
        print(f'[{mod['full_name']}] ERROR')
        print(e)
        raise

async def process_mod_limited(mod, page, index, res):
    async with sem:
        return await asyncio.to_thread(process_mod, mod, page, index, res)

async def process_mods():
    reset_icons()

    tasks = []
    result = []
    page = 1

    while True:
        res = query("/search/repositories", { "q": f"topic:{topic} archived:false template:false pushed:>={lastPushDate}", "per_page": perPage, "page": page, "sort": "updated" })
        mods = res['items']

        print(f'[{int(page/math.ceil(res['total_count'] / perPage)*100)}%] [page {page}] quering page...')

        mods = [mod for mod in mods if not mod['full_name'].startswith(nameBlacklist)]
        mods = [mod for mod in mods if not mod['full_name'] in blacklist]

        for index, mod in enumerate(mods):
            tasks.append(asyncio.create_task(process_mod_limited(mod, page, index, res)))

        if page == math.ceil(res['total_count'] / perPage):
            break

        page += 1

    result = await asyncio.gather(*tasks)

    print(f'Found {len(result)} mods via topic: {topic}')
    return result

result = asyncio.run(process_mods())
result = [r for r in result if not r == None]
result = [{ k: v for k, v in d.items() if v is not None } for d in result]

result.sort(key=lambda m: (-m['stars'], m['updated_at']))

with open('data/mods.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)