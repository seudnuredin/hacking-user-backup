import requests
import json
import time
import re

headers = {
  'Accept': 'application/json'
}

def get_structured_scopes(handle):
    program_structured_scopes_body_list = list()
    next_link = f'https://api.hackerone.com/v1/hackers/programs/{handle}/structured_scopes?page%5Bnumber%5D=1'
    while True:
        time.sleep(0.11)

        program_structured_scopes_response = requests.get(
          next_link,
          auth=('<username>', '<token>'),
          headers = headers
        )

        program_structured_scopes_body = program_structured_scopes_response.json()
        program_structured_scopes_body_list.append(program_structured_scopes_body)

        if "next" in program_structured_scopes_body["links"].keys():
            next_link = program_structured_scopes_body["links"]["next"]
        else:
            return program_structured_scopes_body_list

programs_and_their_scopes_output_count = 1
next_link = f'https://api.hackerone.com/v1/hackers/programs?page%5Bnumber%5D=1'
while True:
    time.sleep(0.11)
    programs_response = requests.get(
          next_link,
          auth=('<username>', '<token>'),
          headers = headers
        )
    
    programs_response_body = programs_response.json()
    programs_and_their_scopes = list()

    for program in programs_response_body["data"]:
        programs_and_their_scopes.append({"program": program, "scope": get_structured_scopes(program["attributes"]["handle"])})
        # print(json.dumps(get_structured_scopes(program["attributes"]["handle"])))
        # break

    with open(f"programs_and_their_scopes_output_{programs_and_their_scopes_output_count}.json", "w") as file:
        file.write(json.dumps(programs_and_their_scopes))
    
    programs_and_their_scopes_output_count += 1

    if "next" in programs_response_body["links"].keys():
        next_link = programs_response_body["links"]["next"]
    else:
        break

    # remove the break after you're done with testing
    # break
