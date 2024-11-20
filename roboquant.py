import json
import os

json_path = os.path.join('/Users/ariel/Downloads/Roboquant (1)/general_e3f6ac9b-0370-4102-a377-014692658832', 'general_page_1.json')
new_json_path = os.path.join('/Users/ariel/Downloads/Roboquant (1)/general_e3f6ac9b-0370-4102-a377-014692658832', 'new_format.json')
new_json_file = []

with open(json_path, 'r') as f:
    json_file = json.load(f)
    for message in json_file:
        json_obj = {'timestamp': message['timestamp'], 'userName': message['userName'], 'content': message['content']}
        new_json_file.append(json_obj)

with open(new_json_path, 'w') as f:
    f.write(json.dumps(new_json_file))

