import re
import requests
import json
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.spinner import Spinner
import os
import sys
import subprocess
import readline


MODEL = 'gpt-4o'

token = None
messages = []
console = Console()
client_id = 'Iv1.b507a08c87ecfe98'

access_token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.copilot_token')

def setup():
    resp = requests.post('https://github.com/login/device/code', headers={
            'accept': 'application/json',
            'editor-version': 'Neovim/0.6.1',
            'editor-plugin-version': 'copilot.vim/1.31.0',
            'content-type': 'application/json',
            'user-agent': 'GithubCopilot/1.194.0',
            'accept-encoding': 'gzip,deflate,br'
        }, data=f'{{"client_id":"{client_id}","scope":"read:user"}}')


    # Parse the response json, isolating the device_code, user_code, and verification_uri
    resp_json = resp.json()
    device_code = resp_json.get('device_code')
    user_code = resp_json.get('user_code')
    verification_uri = resp_json.get('verification_uri')

    # Print the user code and verification uri
    print(f'Please visit {verification_uri} and enter code {user_code} to authenticate.')


    while True:
        time.sleep(5)
        resp = requests.post('https://github.com/login/oauth/access_token', headers={
            'accept': 'application/json',
            'editor-version': 'Neovim/0.6.1',
            'editor-plugin-version': 'copilot.vim/1.31.0',
            'content-type': 'application/json',
            'user-agent': 'GithubCopilot/1.194.0',
            'accept-encoding': 'gzip,deflate,br'
            }, data=f'{{"client_id":"{client_id}","device_code":"{device_code}","grant_type":"urn:ietf:params:oauth:grant-type:device_code"}}')

        # Parse the response json, isolating the access_token
        resp_json = resp.json()
        access_token = resp_json.get('access_token')

        if access_token:
            break

    # Save the access token to a file
    with open(access_token_path, 'w') as f:
        f.write(access_token)

    print('Authentication success!')


def get_token():
    global token
        # Check if the .copilot_token file exists
    while True:
        try:
            with open(access_token_path, 'r') as f:
                access_token = f.read()
                break
        except FileNotFoundError:
            setup()
    # Get a session with the access token
    resp = requests.get('https://api.github.com/copilot_internal/v2/token', headers={
        'authorization': f'token {access_token}',
        'editor-version': 'Neovim/0.6.1',
        'editor-plugin-version': 'copilot.vim/1.31.0',
        'user-agent': 'GithubCopilot/1.194.0'
    })

    # Parse the response json, isolating the token
    resp_json = resp.json()
    token = resp_json.get('token')

def chat(message):
    global token, messages, console
    # If the token is None, get a new one
    if token is None:
        get_token()

    messages.append({
        "content": str(message),
        "role": "user"
    })

    # Show a spinner while waiting for the response
    with console.status(''):
        try:
            resp = requests.post('https://api.githubcopilot.com/chat/completions', headers={
                    'authorization': f'Bearer {token}',
                    'Editor-Version': 'vscode/1.80.1',
                }, json={
                    'intent': False,
                    'model': MODEL,
                    'temperature': 0,
                    'top_p': 1,
                    'n': 1,
                    'stream': False,
                    'messages': messages
                })
        except requests.exceptions.ConnectionError:
            return ''

        try:
            result = resp.json()['choices'][0]['message']['content']
        except:
            print(resp.status_code)
            print(resp.text)
            return ''

        messages.append({
            "content": result,
            "role": "assistant"
        })

    console.print(Markdown(result))


def main():
    global messages
    get_token()
    while True:
        user = input('\33[35m~> \33[33m')
        print('\033[0m', end='', flush=True)
        if user == 'exit':
            break
        if user == 'clear':
            messages = []
            # Clear the terminal
            console.clear()
            continue
        if user.startswith('load '):
            try:
                filename = ' '.join(user.split()[1:])
                if not filename:
                    print('Please specify a file to open')
                    continue
                with open(filename, 'r') as f:
                    messages.append({
                        "content": f"Use this file named {filename} for future reference:\n\n" + f.read(),
                        "role": "user"
                    })
                    print("File opened")
                continue
            except FileNotFoundError:
                print('File not found')
                continue
        if user.startswith('save '):
            # Find the largest code block from the last response and save it to a file
            filename = ' '.join(user.split()[1:])
            if not filename:
                print('Please specify a file to save to')
                continue
            code_blocks = []
            for message in messages[::-1]:
                if message['role'] == 'assistant':
                    code_blocks.extend(block.group(1) for block in re.finditer(r'\n```\w*\n(.*?\n)```', message['content'], re.DOTALL))
                if code_blocks:
                    break
            if code_blocks:
                with open(filename, 'w') as f:
                    f.write(max(code_blocks, key=len))
                print(f"Code saved to {filename}")
            else:
                print('No code to save')
            continue
        if user.startswith('sh '):
            # Run a shell command, and save the output to the messages
            command = ' '.join(user.split()[1:])
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            message_result = f"The command `{command}` was run. The output is:\n\n```\n{result.stdout.decode()}\n```."
            if result.stderr:
                message_result += f"\n\nError:\n\n```\n{result.stderr.decode()}\n```."
            console.print(result.stdout.decode())
            if result.stderr:
                console.print("Error: " + result.stderr.decode())
            messages.append({
                "content": message_result,
                "role": "user"
            })
            continue
        if user == 'run':
            # Find the largest code block from the last response and run it
            code_blocks = []
            for message in messages[::-1]:
                if message['role'] == 'assistant':
                    code_blocks.extend((block.group(1), block.group(2), len(block.group(2))) for block in re.finditer(r'\n```(\w+)\n(.*?\n)```', message['content'], re.DOTALL))
                if code_blocks:
                    break
            if code_blocks:
                code_block = max(code_blocks, key=lambda x: x[2])
                with open('.tmp.script', 'w') as f:
                    f.write(code_block[1])
                result = subprocess.run([code_block[0], '.tmp.script'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                console.print(result.stdout.decode())
                if result.stderr:
                    console.print("Error: " + result.stderr.decode())
                message_result = f"The command `{code_block[0]} script.tmp` was run, where script.tmp was the last provided code snippet. The output is:\n\n```\n{result.stdout.decode()}\n```."
                if result.stderr:
                    message_result += f"\n\nError:\n\n```\n{result.stderr.decode()}\n```."
                else:
                    message_result += "\n\nNo errors were encountered."
                messages.append({
                    "content": message_result,
                    "role": "user"
                })
                os.remove('.tmp.script')
            else:
                console.print('No code to run')
            continue
        if user == "help":
            print("Special commands:")
            print("    load <filename>: Load a file and use it for future reference")
            print("    save <filename>: Save the last code block to a file")
            print("    sh <command>: Run a shell command (saves the output for future reference)")
            print("    run: Run the code from the last response")
            print("    clear: Clear the terminal and forget all previous messages")
            print("    exit: Exit chat")
            print()
            continue
        chat(user)


if __name__ == '__main__':
    main()
