import requests

url = "https://nc.me.pi2s2.it/nextcloud/ocs/v1.php/cloud/users?search=csicari@unime.it"

payload={}
headers = {
  'OCS-APIRequest': 'true',
  'Accept': 'application/json',
}

response = requests.request("GET", url, auth=('deckbot', 'Deckbotfcrl4b@'), headers=headers, data=payload)

print(response.text)
