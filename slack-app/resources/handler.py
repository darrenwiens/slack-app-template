import base64
import json
import os

import urllib.parse
import urllib
from urllib import request, parse

SLACK_BEARER_TOKEN = os.environ['SLACK_BEARER_TOKEN']
GH_PERSONAL_ACCESS_TOKEN = os.environ['GH_PERSONAL_ACCESS_TOKEN']

def create_modal(body, bearer_token):
    """ Create the modal in Slack """
    
    req =  request.Request('https://slack.com/api/views.open', data=json.dumps(body).encode('utf-8'))
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Authorization', f'Bearer {bearer_token}')

def create_gist(filename, description, content, GH_PERSONAL_ACCESS_TOKEN=None):
    content = json.dumps(json.loads(content))
    body = {
        "files": {filename: {'content': content}},
        "description": description,
        "public": False
    }
    req =  request.Request('https://api.github.com/gists', data=json.dumps(body).encode('utf-8'))
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('Authorization', f'token {GH_PERSONAL_ACCESS_TOKEN}')

def lambda_handler(event, context):
    body_dict = urllib.parse.parse_qs(base64.b64decode(event.get('body')).decode("utf-8"))

    payload_dict = {}
    if body_dict.get('payload'):
        payload_dict = json.loads(body_dict.get('payload')[0])

    if body_dict.get('command'):
        """ If the request body contains key 'command', it is directly from the slash command. 
        Results submitted from shortcut modal should also come here. """

        if body_dict.get('command'):
            trigger_id = body_dict.get('trigger_id')[0]
            team_id = body_dict.get('team_id')[0]
            response_url = body_dict.get('response_url')[0]
        else:
            trigger_id = payload_dict.get('trigger_id')
            team_id = payload_dict.get('team')['id']
            response_url = payload_dict.get('response_urls')[0]['response_url']

        body = {
            "trigger_id": trigger_id,
            "view": {
                "type": "modal",
                "callback_id": "shortcut_modal",
                "title": {
                    "type": "plain_text",
                    "text": "/gist"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Submit"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "blocks": [
                    {
                        "type": "input",
                        "element": {
                            "type": "plain_text_input",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Filename inclusing extension..."
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Filename"
                        },
                        "block_id": "filename_text"
                    },
                    {
                        "type": "input",
                        "element": {
                            "type": "plain_text_input",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Gist description..."
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Description"
                        },
                        "block_id": "description_text"
                    },
                    {
            			"type": "input",
            			"element": {
            				"type": "plain_text_input",
            				"multiline": True
            			},
            			"label": {
            				"type": "plain_text",
            				"text": "Gist Content",
            				"emoji": True
            			},
                        "block_id": "content_text"
            		}
                ]
            }
        }
        create_modal(body, SLACK_BEARER_TOKEN)
    
    elif body_dict.get('payload'):
        """ Interaction payloads contain key 'payload' """
        body_json = json.loads(body_dict.get('payload')[0])
        
        if body_json.get('type') == 'view_submission':
            """ View submission payloads are sent on submit button click """
            state = body_json["view"]["state"]["values"]
            filename = state["filename_text"][list(state["filename_text"].keys())[0]]["value"]
            description = state["description_text"][list(state["description_text"].keys())[0]]["value"]
            gist_content = state["content_text"][list(state["content_text"].keys())[0]]["value"]
            
            create_gist(filename, description, gist_content)
            
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }