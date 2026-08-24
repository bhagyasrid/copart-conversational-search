import re
from .models import Filters

MAKES=("Toyota","Honda","Ford","Tesla","Jeep","Chevrolet","Nissan","Hyundai","Kia","BMW","Mercedes-Benz","Audi","Lexus","Mazda","Subaru","Volkswagen","Ram","GMC","Volvo","Chrysler","Dodge","Porsche","Rivian")
BODIES=("SUV","Sedan","Truck","Coupe","Van","Minivan","Wagon","Hatchback","Convertible")
STATES={"texas":"TX","california":"CA","arizona":"AZ","colorado":"CO","florida":"FL","georgia":"GA","illinois":"IL","nevada":"NV","new york":"NY","washington":"WA"}

def refine_with_rules(text:str,current:Filters)->Filters:
    q=text.lower(); data=current.model_dump(); add=bool(re.search(r"\b(or|also|include|add)\b",q))
    if re.search(r"reset|start over|clear (all|search|filters)|show (me )?(all|every) (cars?|vehicles?|inventory)",q): return Filters()
    def set_list(key:str,values:list[str]): data[key]=list(dict.fromkeys([*data[key],*values])) if add else values
    makes=[x for x in MAKES if x.lower() in q]
    if makes:
        if re.search(r"\b(no|exclude|without)\b",q): data["excludedMakes"]=list(dict.fromkeys([*data["excludedMakes"],*makes]))
        else: set_list("makes",makes)
    bodies=[x for x in BODIES if re.search(rf"\b{re.escape(x.lower())}s?\b",q)]
    if bodies:set_list("bodies",bodies)
    locations=[code for name,code in STATES.items() if re.search(rf"\b{re.escape(name)}\b",q)]
    if locations:set_list("states",locations)
    year_range=re.search(r"(?:between|from)?\s*(19\d{2}|20\d{2})\s*(?:and|to|through|-)\s*(19\d{2}|20\d{2})",q)
    newer=re.search(r"(19\d{2}|20\d{2})\s*(?:or newer|\+|and newer|or later)",q)
    older=re.search(r"(?:before|through|up to|no newer than)\s*(19\d{2}|20\d{2})|(19\d{2}|20\d{2})\s*or older",q)
    exact=re.search(r"(?:model(?:\s+year)?\s*)?(19\d{2}|20\d{2})\s*(?:model|models|model year|only|year)?\b",q)
    if year_range:data["minYear"]=min(map(int,year_range.groups()));data["maxYear"]=max(map(int,year_range.groups()))
    elif newer:data["minYear"]=int(newer.group(1));data["maxYear"]=None
    elif older:data["maxYear"]=int(older.group(1) or older.group(2));data["minYear"]=None
    elif exact:data["minYear"]=int(exact.group(1));data["maxYear"]=int(exact.group(1))
    price=re.search(r"(?:under|below|less than|max(?:imum)?|budget(?: of)?)\s*\$?([\d,.]+)\s*(k|grand)?",q)
    if price:data["maxPrice"]=round(float(price.group(1).replace(",",""))*(1000 if price.group(2) else 1));data["minPrice"]=None
    fuels=[x for x in ("Gas","Diesel","Hybrid","Electric") if re.search(rf"\b{x.lower()}\b",q)]
    if "gasoline" in q and "Gas" not in fuels:fuels.append("Gas")
    if fuels:set_list("fuels",fuels)
    drives=[x for x in ("FWD","RWD","AWD","4WD") if re.search(rf"\b{x.lower()}\b",q)]
    if drives:set_list("drives",drives)
    if re.search(r"\b(automobile|automobiles|car|cars)\b",q):set_list("vehicleTypes",["Automobile"])
    cylinder=re.search(r"\b(0|4|6|8)[ -]?(?:cylinder|cylinders|cyl)\b",q)
    if cylinder:data["cylinders"]=[int(cylinder.group(1))]
    origins=[country for country in ("United States","Japan","Germany","South Korea","Sweden") if f"made in {country.lower()}" in q or f"manufactured in {country.lower()}" in q]
    if origins:set_list("manufacturedIn",origins)
    if "lowest price" in q or "cheapest" in q:data["sort"]="price-asc"
    return Filters.model_validate(data)
