import json
from curl_cffi import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

tours = {
    'Premier_League': '17', 
    'La_Liga': '8', 
    'Serie_A': '23', 
    'Bundesliga': '35', 
    'Ligue_1': '34'
}

results = {}

print("Starting fetch...")
for name, t_id in tours.items():
    print(f"Fetching {name}...")
    url = f'https://www.sofascore.com/api/v1/unique-tournament/{t_id}/seasons'
    try:
        res = requests.get(url, headers=headers, impersonate="chrome124", timeout=5)
        if res.status_code == 200:
            seasons = res.json().get('seasons', [])
            season_map = {}
            for s in seasons[:3]: 
                s_name = s['name']
                if '/' not in s_name:
                    s_name = s_name.replace("20", "")
                season_map[s['name']] = str(s['id'])
            results[name] = (t_id, season_map)
        else:
            print(f"Failed {name} with code {res.status_code}")
    except Exception as e:
        print(f"Error fetching {name}: {e}")

print("TOP_5_LEAGUES = {")
for k, v in results.items():
    print(f'    "{k}": ("{v[0]}", {v[1]}),')
print("}")
