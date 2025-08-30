import re

# Minimal, precise Markdown v2 escape (no leakage)
MDV2_SPECIALS = r"_*[]()~`>#+-=|{}.!\\"
MDV2_RE = re.compile("([_%s])" % re.escape(MDV2_SPECIALS.replace("_", "")))

def mdv2(text: str) -> str:
    if text is None:
        return ""
    # Escape underscore explicitly first (common in usernames)
    text = text.replace("_", "\\_")
    # Escape remaining specials
    text = MDV2_RE.sub(r"\\\1", text)
    return text

def with_footer(text: str) -> str:
    footer = "\n\nManaged by @Bank\\_rats | @Migos\\_B\\_Fx254"
    return f"{text}{footer}"
