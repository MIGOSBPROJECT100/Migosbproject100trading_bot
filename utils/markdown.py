import re

# Minimal, precise Markdown v2 escape (no leakage)
MDV2_SPECIALS = r"_*[]()~`>#+-=|{}.!\\"
MDV2_RE = re.compile("([%s])" % re.escape(MDV2_SPECIALS))

def mdv2(text: str) -> str:
    if text is None:
        return ""
    # Escape all MarkdownV2 specials in one go
    return MDV2_RE.sub(r"\\\1", text)

def with_footer(text: str) -> str:
    footer = "\n\nManaged by @Bank_rats | @Migos_B_Fx254"
    # Run through mdv2 ONCE, so no manual escapes ever leak
    return mdv2(f"{text}{footer}")
