from __future__ import annotations

import json
import re
import unicodedata


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.replace(chr(305), "i")


def request_needs_tools(user_text: str) -> bool:
    """Detect explicit computer-operation requests in Turkish and English."""
    text = _normalize(user_text)

    # Strong phrases that unambiguously ask the agent to operate the device.
    strong_phrases = (
        "use your push tools", "use push tools", "with your push tools",
        "switch to action mode", "enable action mode",
        "current working directory", "working directory",
        "inspect the current environment", "inspect this computer",
        "on my computer", "on this computer", "on the windows machine",
        "list files", "list folders", "show files", "show folders",
        "run a command", "run this command", "execute this command",
        "run powershell", "run cmd", "terminal command",
        "check the python version", "check python version",
        "check the git version", "check git version",
        "print the current date", "current date and time",
        "take a screenshot", "inspect the screen",
        "read this file", "create a file", "write to a file",
        "edit this file", "delete this file", "rename this file",
        "download this file", "upload this file",
        "dosya listele", "klasor listele", "terminal komutu",
        "powershell komutu", "komut calistir", "ekran goruntusu al",
        "bilgisayari kontrol et", "calisma dizinini goster",
    )
    if any(phrase in text for phrase in strong_phrases):
        return True

    # Existing Turkish morphology-aware patterns.
    file_or_folder = (
        r"\b(dosya|dosyalar|dosyalari|dosyasini|dosyanin|dosyaya|"
        r"dosyadaki|klasor|klasoru|klasorun|klasorundeki|dizin|"
        r"dizini|dizindeki|dizinindeki)\b"
    )
    tr_action = (
        r"\b(olustur|yarat|yaz|kaydet|oku|goster|listele|soyle|"
        r"belirt|say|sil|degistir|duzenle|icerigini|ac|calistir|"
        r"tikla|indir|kopyala|tasi|yeniden adlandir)\b"
    )
    if re.search(file_or_folder + r".*" + tr_action, text) or re.search(
        tr_action + r".*" + file_or_folder, text
    ):
        return True

    # English action verbs paired with a concrete device, file, shell, or
    # environment target. Generic questions such as "explain how APIs work"
    # therefore remain in CHAT mode.
    action = (
        r"\b(inspect|list|read|create|edit|overwrite|delete|move|rename|"
        r"download|upload|open|close|launch|run|execute|click|type|press|"
        r"check|print|show|get|find|search|take)\b"
    )
    target = (
        r"\b(file|files|folder|folders|directory|directories|terminal|"
        r"powershell|cmd|command|computer|screen|desktop|mouse|keyboard|"
        r"python|git|version|environment|date|time|process|application|"
        r"program|window|browser|device)\b"
    )
    if re.search(action, text) and re.search(target, text):
        return True

    # Explicit paths combined with an operation.
    has_path = bool(re.search(
        r"(?:[a-z]:\\|\\\\)[^\s\"']+|[\w.-]+\.(?:txt|md|json|py|js|html|css|csv|log)\b",
        text,
    ))
    if has_path and re.search(action + "|" + tr_action, text):
        return True

    return False


def parse_groq_route(raw: str) -> str:
    """Parse a strict CHAT/ACTION response, tolerating JSON or short wrappers."""
    value = str(raw or "").strip()
    if not value:
        raise ValueError("Groq boş rota döndürdü")

    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        route = str(payload.get("route", "")).strip().casefold()
        if route in ("chat", "action"):
            return route

    cleaned = value.strip("`'\\" ).strip()
    if cleaned.casefold() in ("chat", "action"):
        return cleaned.casefold()

    # Some providers wrap the final one-word answer in a short sentence.
    lines = [line.strip().strip("`'\\" ) for line in value.splitlines() if line.strip()]
    if lines:
        final_line = lines[-1].casefold()
        match = re.fullmatch(r"(?:route\s*[:=]\s*)?(chat|action)[.!]?", final_line)
        if match:
            return match.group(1)

    raise ValueError(f"Groq geçersiz rota döndürdü: {value[:160]}")
