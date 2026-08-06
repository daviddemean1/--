import json
import os
import requests

DATA_FILE = "bugcrowd_data.json"
STATE_FILE = "previous_scopes.json"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def extract_scopes(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    extracted = {}
    for program_handle, details in data.items():
        program_name = details.get("name", program_handle)
        scopes = details.get("scopes", [])
        
        targets = []
        for scope in scopes:
            target = scope.get("target")
            scope_type = scope.get("type")
            if target:
                targets.append(f"[{scope_type}] {target}")
        
        if targets:
            extracted[program_name] = sorted(list(set(targets)))
            
    return extracted

def send_alert(new_targets):
    if not WEBHOOK_URL:
        print("[!] Webhook URL not set.")
        return

    embed_fields = []
    for prog, targets in new_targets.items():
        field_value = "\n".join(targets[:10]) # Limit to avoid payload size limits
        if len(targets) > 10:
            field_value += f"\n... and {len(targets) - 10} more."
            
        embed_fields.append({
            "name": f"🎯 Program: {prog}",
            "value": f"```\n{field_value}\n```",
            "inline": False
        })

    payload = {
        "username": "Bugcrowd Scope Monitor",
        "avatar_url": "https://bugcrowd.com/favicon.ico",
        "content": "🚨 **New Bugcrowd Target(s) Discovered!**",
        "embeds": [{
            "color": 3066993,
            "fields": embed_fields
        }]
    }

    requests.post(WEBHOOK_URL, json=payload)

def main():
    current_state = extract_scopes(DATA_FILE)
    
    previous_state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            previous_state = json.load(f)

    diff = {}
    for prog, targets in current_state.items():
        if prog not in previous_state:
            diff[prog] = targets
        else:
            new_in_prog = set(targets) - set(previous_state[prog])
            if new_in_prog:
                diff[prog] = list(new_in_prog)

    if diff:
        print(f"[+] Found changes in {len(diff)} programs. Sending notifications...")
        send_alert(diff)
        
        # Update state
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_state, f, indent=4)
    else:
        print("[*] No new scopes detected.")

if __name__ == "__main__":
    main()
