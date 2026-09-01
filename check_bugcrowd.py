import json
import os
import requests

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
STATE_FILE = "known_programs.json"

BOUNTY_DATA_URL = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/bugcrowd_data.json"


def fetch_bugcrowd_programs():
  try:
    response = requests.get(BOUNTY_DATA_URL, timeout=30)
    response.raise_for_status()
    return response.json()
  except Exception as e:
    print(f"[-] Error fetching data from bounty-targets-data: {e}")
    return []


def load_known_programs():
  if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
      try:
        return set(json.load(f))
      except Exception:
        return set()
  return set()


def save_known_programs(known_ids):
  with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(list(known_ids), f, indent=2)


def send_discord_notification(program):
  name = program.get("name", "Unknown Program")
  url = program.get("url", "")
  allows_disclosure = program.get("allows_disclosure", False)
  safe_harbor = program.get("safe_harbor", "N/A")

  embed = {
      "title": f"🚨 New Bugcrowd Target: {name}",
      "url": url,
      "color": 15158332,
      "fields": [
          {
              "name": "Program URL",
              "value": url if url else "N/A",
              "inline": False,
          },
          {
              "name": "Allows Disclosure",
              "value": "Yes" if allows_disclosure else "No",
              "inline": True,
          },
          {"name": "Safe Harbor", "value": str(safe_harbor), "inline": True},
      ],
  }

  payload = {"username": "Bugcrowd Radar", "embeds": [embed]}

  res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
  if res.status_code in [200, 204]:
    print(f"[+] Notified Discord for: {name}")
  else:
    print(f"[-] Failed to send notification: {res.status_code}, {res.text}")


def main():
  if not DISCORD_WEBHOOK_URL:
    print("[-] DISCORD_WEBHOOK_URL environment variable is missing.")
    return

  programs = fetch_bugcrowd_programs()
  if not programs:
    print("[-] No programs retrieved.")
    return

  known_ids = load_known_programs()
  is_first_run = len(known_ids) == 0

  current_ids = set()
  new_programs = []

  for prog in programs:
    prog_id = prog.get("url") or prog.get("name")
    if not prog_id:
      continue

    current_ids.add(prog_id)
    if not is_first_run and prog_id not in known_ids:
      new_programs.append(prog)

  if is_first_run:
    print(
        f"[+] First run initialized with {len(current_ids)} programs. State"
        " saved."
    )
  else:
    print(f"[+] Found {len(new_programs)} new programs.")
    for prog in new_programs:
      send_discord_notification(prog)

  updated_ids = known_ids.union(current_ids)
  save_known_programs(updated_ids)


if __name__ == "__main__":
  main()
