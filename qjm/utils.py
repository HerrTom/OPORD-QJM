import requests
import json
import yaml


def gist(content):
    with open('./token.yaml', 'r') as f:
        data = yaml.safe_load(f)
    token = data['token']
    gist_id = data['gist_id']
    filename = data['filename']

    headers = {'Authorization': f'Bearer {token}'}
    r = requests.patch('https://api.github.com/gists/' + gist_id,
                       data=json.dumps({'files':{
                           filename:{
                                    "content":content
                                    }
                               }
                               }),
                               headers=headers)