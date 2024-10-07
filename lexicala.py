import os

import requests

from variables import Keys

prefix_url = "https://lexicala1.p.rapidapi.com/"
# function = "languages"
# function = "test"
text = "יריקה"
function = f"search?source=global&language=he&text={text}&analyzed=true"

url = prefix_url + function

headers = {
	"x-rapidapi-key": Keys.rapidapi_key,
	"x-rapidapi-host": "lexicala1.p.rapidapi.com"
}

response1 = requests.get(url, headers=headers)
print(response1.json())

entry_id = response1.json()['results'][0]['id']
description = response1.json()['results'][0]['senses'][0]['definition']

new_url = prefix_url + f"entries/{entry_id}"
response = requests.get(new_url, headers=headers)

gender = response.json()['headword']['gender']
plurial = response.json()['headword']['inflections'][0]['text']
english = response.json()['senses'][0]['translations']['en']['text']
french = response.json()['senses'][0]['translations']['fr']['text']
# print(response.json())