import json, time, webbrowser
from pathlib import Path
import requests
from .cache import ROOT, ensure

# Public Microsoft OAuth application/client ID used by the Prism/Atlas launcher lineage.
# This is an application identifier, not a client secret.
MSA_CLIENT_ID = "c36a9fb6-4f2a-41ff-90bd-ae7cc92031eb"
MS_TENANT = "consumers"
DEVICE_CODE_URL = f"https://login.microsoftonline.com/{MS_TENANT}/oauth2/v2.0/devicecode"
TOKEN_URL = f"https://login.microsoftonline.com/{MS_TENANT}/oauth2/v2.0/token"
SCOPE = "XboxLive.signin offline_access"
ACCOUNT_FILE = ROOT / "account.json"
ACCOUNTS_FILE = ROOT / "accounts.json"
UA = "mcli/0.2"

class AuthError(RuntimeError): pass

def _post(url, **kwargs):
    r = requests.post(url, timeout=30, headers={"User-Agent": UA}, **kwargs)
    return r

def _load_store():
    ensure()
    try:
        data=json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
        if isinstance(data,dict) and "accounts" in data:
            return data
    except Exception:
        pass
    # Migrate the v0.8.x single-account file automatically.
    try:
        old=json.loads(ACCOUNT_FILE.read_text(encoding="utf-8"))
        name=(old.get("profile") or {}).get("name","default")
        data={"active":name,"accounts":{name:old}}
        ACCOUNTS_FILE.write_text(json.dumps(data,indent=2),encoding="utf-8")
        return data
    except Exception:
        return {"active":None,"accounts":{}}

def _save_store(data):
    ensure()
    ACCOUNTS_FILE.write_text(json.dumps(data,indent=2),encoding="utf-8")

def _save(account, alias=None):
    data=_load_store()
    profile=account.get("profile") or {}
    key=alias or profile.get("name") or profile.get("id") or "default"
    data["accounts"][key]=account
    data["active"]=key
    _save_store(data)


def list_accounts():
    data=_load_store()
    return data.get("active"), data.get("accounts",{})

def load_account(alias=None):
    data=_load_store()
    key=alias or data.get("active")
    if not key:
        return None
    return data.get("accounts",{}).get(key)

def use_account(alias):
    data=_load_store()
    if alias not in data.get("accounts",{}):
        # permit exact profile-name/id lookup
        found=None
        for k,a in data.get("accounts",{}).items():
            p=a.get("profile") or {}
            if alias in (p.get("name"),p.get("id")):
                found=k; break
        if not found:
            raise AuthError(f"Unknown account: {alias}")
        alias=found
    data["active"]=alias
    _save_store(data)
    return data["accounts"][alias]

def remove_account(alias):
    data=_load_store()
    if alias not in data.get("accounts",{}):
        raise AuthError(f"Unknown account: {alias}")
    removed=data["accounts"].pop(alias)
    if data.get("active")==alias:
        data["active"]=next(iter(data["accounts"]),None)
    _save_store(data)
    return removed

def logout():
    data=_load_store()
    active=data.get("active")
    if active and active in data.get("accounts",{}):
        data["accounts"].pop(active)
        data["active"]=next(iter(data["accounts"]),None)
        _save_store(data)

def _device_login():
    r = _post(DEVICE_CODE_URL, data={"client_id": MSA_CLIENT_ID, "scope": SCOPE})
    r.raise_for_status()
    dc = r.json()
    print("\nMicrosoft sign-in")
    print("Open:", dc.get("verification_uri", "https://microsoft.com/link"))
    print("Code:", dc["user_code"])
    print()
    try:
        webbrowser.open(dc.get("verification_uri", "https://microsoft.com/link"))
    except Exception:
        pass

    deadline = time.time() + int(dc["expires_in"])
    interval = int(dc.get("interval", 5))
    while time.time() < deadline:
        time.sleep(interval)
        tr = _post(TOKEN_URL, data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": MSA_CLIENT_ID,
            "device_code": dc["device_code"],
        })
        data = tr.json()
        if tr.ok:
            return data
        err = data.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        raise AuthError(data.get("error_description", err or "Microsoft authentication failed"))
    raise AuthError("Microsoft device code expired")

def _refresh(refresh_token):
    r = _post(TOKEN_URL, data={
        "client_id": MSA_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": SCOPE,
    })
    if not r.ok:
        raise AuthError(r.text)
    return r.json()

def _minecraft_chain(ms_access_token):
    # Microsoft -> Xbox Live
    r = _post("https://user.auth.xboxlive.com/user/authenticate", json={
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": "d=" + ms_access_token,
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
    })
    r.raise_for_status()
    xbl = r.json()
    user_hash = xbl["DisplayClaims"]["xui"][0]["uhs"]

    # Xbox Live -> XSTS for Minecraft services
    r = _post("https://xsts.auth.xboxlive.com/xsts/authorize", json={
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [xbl["Token"]],
        },
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT",
    })
    if not r.ok:
        raise AuthError("XSTS authentication failed: " + r.text)
    xsts = r.json()

    # XSTS -> Minecraft access token
    r = _post("https://api.minecraftservices.com/authentication/login_with_xbox", json={
        "identityToken": f"XBL3.0 x={user_hash};{xsts['Token']}"
    })
    r.raise_for_status()
    mc = r.json()

    headers = {"Authorization": "Bearer " + mc["access_token"], "User-Agent": UA}

    # Ownership / entitlements
    er = requests.get("https://api.minecraftservices.com/entitlements/mcstore",
                      headers=headers, timeout=30)
    er.raise_for_status()

    # Java profile
    pr = requests.get("https://api.minecraftservices.com/minecraft/profile",
                      headers=headers, timeout=30)
    if pr.status_code == 404:
        raise AuthError("Microsoft account authenticated, but no Minecraft Java profile was returned.")
    pr.raise_for_status()
    profile = pr.json()

    return {
        "minecraft_access_token": mc["access_token"],
        "minecraft_expires_in": mc.get("expires_in"),
        "profile": profile,
        "entitlements": er.json(),
    }

def login(alias=None):
    ms = _device_login()
    mc = _minecraft_chain(ms["access_token"])
    account = {
        "client_id": MSA_CLIENT_ID,
        "refresh_token": ms.get("refresh_token"),
        "profile": mc["profile"],
        "minecraft_access_token": mc["minecraft_access_token"],
        "authenticated_at": int(time.time()),
    }
    _save(account, alias)
    return account

def refresh(alias=None):
    account = load_account(alias)
    if not account or not account.get("refresh_token"):
        raise AuthError("No saved Microsoft account. Run: mcli login")
    ms = _refresh(account["refresh_token"])
    mc = _minecraft_chain(ms["access_token"])
    account.update({
        "refresh_token": ms.get("refresh_token", account["refresh_token"]),
        "profile": mc["profile"],
        "minecraft_access_token": mc["minecraft_access_token"],
        "authenticated_at": int(time.time()),
    })
    data=_load_store()
    key=alias or data.get("active")
    if key:
        data["accounts"][key]=account
        _save_store(data)
    else:
        _save(account)
    return account
