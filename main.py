import functions_framework
import json
import logging

from flask import jsonify
import requests

# Define key variables used by the process
#===================================================
CONTROL_ROOM = 'https://your_control_room.my.automationanywhere.digital'
CR_USERNAME = 'your.user.name'
CR_PASSWORD = 'your.password'
RUNASUSERS  = '[327]'
FORMDATA = ""       # will hold data submitted by form
FORMNAME = ""       # will hold the name of the form
FILEID = 0          # will hold the bot id to run

@functions_framework.http
def hello_http(request):
    print("Starting processing.....")
    request_args = request.args
    content_type = request.headers["content-type"]
    
    # get token to access control room
    #================================================
    jsonpkg = '{"username": "' + CR_USERNAME + '", "password": "' + CR_PASSWORD + '"}'
    endpoint = '/v1/authentication'
    headers = {'Content-Type': 'application/json'}  
    url = CONTROL_ROOM + endpoint
    result = requests.post(url=url, headers=headers, data=jsonpkg, verify=True) 
    data = result.json()
    token = data["token"]
    headers = '{"Content-Type": "application/json", "X-Authorization": "' + token + '"}'
    headers = json.loads(headers)

    # get data sent to endpoint
    #================================================
    if content_type == "application/json":
        request_json = request.get_json(silent=True)
        FORMDATA = json.dumps(request_json)
    elif "multipart/form-data" in content_type:
        data = ""
        formdata = request.form.to_dict()
        print(formdata["rawRequest"])
        #for key, value in formdata.items():
        #    print(key, ":", value)
        FORMDATA = formdata["rawRequest"]
        FORMDATA = json.dumps(FORMDATA)
        if FORMDATA[:2] == '"{':
            FORMDATA = FORMDATA.replace('"{', '{', 1)
            FORMDATA = '}'.join(FORMDATA.rsplit('}"', 1))
        FORMNAME = formdata["formTitle"]
    else:
        FORMDATA = '{"Error : "Unhandled content type"}'
    print(FORMDATA)
    print(FORMNAME)

     # get bot id (bot & form names must match)
    #================================================
    endpoint = '/v2/repository/file/list'
    url = CONTROL_ROOM + endpoint
    jsonpkg = '{"filter": {"operator": "substring", "field": "name", "value": "' + FORMNAME + '" }}'
    print(jsonpkg)
    result = requests.post(url=url, headers=headers, data=jsonpkg, verify=True) 
    data = result.json()
    FILEID = data["list"][0]["id"]
    print(FILEID)

    # Prepare body of JSON to be sent
    #================================================
    BOT_JSON = '{"fileId": ' + FILEID + ', "runAsUserIds": ' + RUNASUSERS + ', "poolIds": [], "overrideDefaultDevice": false,  "botInput": { }}'
    print(BOT_JSON)
    BOT_JSON = json.loads(BOT_JSON)
    BOT_JSON["botInput"]["inputJson"] = {"type": "STRING", "string": FORMDATA }
    print(BOT_JSON)

    # trigger bot and send json data
    #================================================
    endpoint = '/v3/automations/deploy'
    url = CONTROL_ROOM + endpoint
    jsonpkg = json.dumps(BOT_JSON)
    result = requests.post(url=url, headers=headers, data=jsonpkg, verify=True) 
    data = result.json()

    return data
