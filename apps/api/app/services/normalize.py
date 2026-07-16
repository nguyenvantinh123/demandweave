import re, unicodedata
CATEGORY_RULES={
 "paper_cups":["coc giay","paper cup","ly giay"],
 "paper_bowls":["to giay","paper bowl"],
 "paper_boxes":["hop giay","paper box","carton"],
 "logistics":["van chuyen","logistics","xe tai","chuyen ve trong"],
 "design":["thiet ke","designer","file in"],
 "capital":["von","dau tu","capital","tai tro"],
}
TYPE_RULES={
 "production_capacity":["du cong suat","cong suat","capacity","xuong"],
 "demand":["can mua","can ","nhu cau","muon mua","order"],
 "logistics_capacity":["xe","van chuyen","logistics","chuyen ve"],
 "skill":["ky nang","thiet ke","designer","ban hang","qa"],
 "capital":["von","dau tu","capital"],
 "inventory":["ton kho","inventory"],
}
def normalize_text(v:str)->str:
    v=unicodedata.normalize("NFKD",v or "")
    v="".join(c for c in v if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9%.,]+"," ",v)).strip()
def parse_number(text:str)->float:
    m=re.search(r"(\d[\d.,]*)\s*(trieu|nghin|k|%)?",normalize_text(text))
    if not m:return 0
    n=float(m.group(1).replace(".","").replace(",","."))
    unit=m.group(2)
    if unit=="trieu":n*=1_000_000
    elif unit in {"nghin","k"}:n*=1_000
    return n
def parse_natural_signal(text:str)->dict:
    n=normalize_text(text)
    category="general"
    for key,words in CATEGORY_RULES.items():
        if any(w in n for w in words): category=key; break
    signal_type="supply"
    for key,words in TYPE_RULES.items():
        if any(w in n for w in words): signal_type=key; break
    quantity=parse_number(text)
    percent=None
    pm=re.search(r"(\d+(?:[.,]\d+)?)\s*%",n)
    if pm: percent=float(pm.group(1).replace(",","."))/100
    locations=[x for x in ["bac ninh","ha noi","thanh hoa","ho chi minh","da nang"] if x in n]
    return {"signal_type":signal_type,"normalized_category":category,"title":text[:180],"quantity":quantity,"unit":"unit","location":locations[0].title() if locations else "","confidence":.65,"attributes":{"parsed_percent":percent,"parser":"deterministic-fallback"}}
