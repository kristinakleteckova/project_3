"""
main.py: třetí projekt do Engeto Online Python Akademie

author: Kristina Kletečková
email: kleteckovakristina@gmail.com
"""
import requests
import bs4
import csv
import sys
import urllib.parse
import locale


zaklad_url = "https://www.volby.cz/pls/ps2017nss/"

def stahni_html(url):
    """
    Stáhne stránku na dané URL a vrátí její HTML jako BeautifulSoup.
    Při chybě vrátí None.
    """
    try:
        odpoved = requests.get(url, timeout=20)
        if odpoved.status_code == 200:
            html_kod = bs4.BeautifulSoup(odpoved.text, "html.parser")
            return html_kod
    except requests.RequestException:
        pass
    return None

def overeni_argumentu(zaklad, url, vystup):
    """
    Zkontroluje vstupní argumenty (počet, platnost URL vůči zaklad_url, příponu .csv)
    a ověří, že se stránka dá stáhnout. Při chybě vypíše hlášku a ukončí skript.
    Vrací stažený BeautifulSoup.
    """
    if len(sys.argv) != 3:
        print("Chyba: Skript vyžaduje 2 argumenty.")
        print("Použití: python main.py <URL> <vystupni_soubor.csv>")
        sys.exit(1)

    if zaklad not in url:
        print("Chyba: nejde o platný odkaz")
        sys.exit(1)

    if not vystup.lower().endswith(".csv"):
        print("Chyba: výstupní soubor musí být ve formátu csv (např. vystup.csv)")
        sys.exit(1)

    html_kod = stahni_html(url)
    if html_kod is None:
        print("Chyba: stránku se nepodařilo stáhnout")
        sys.exit(1)

    print("Vstupní argumenty v pořádku.")
    return html_kod 

def ziskej_odkazy_z_main(html_kod):
    """
    Z hlavní stránky vybere všechny odkazy na obce (href s parametrem xobec=).
    Vrací seznam relativních cest (href).
    """
    odkazy = []
    for a in html_kod.find_all("a", href=True):
        href = a["href"]
        if "xobec=" in href:
            odkazy.append(href)
    return odkazy

def odstraneni_duplicit(odkazy, zaklad=zaklad_url):
    """
    Z relativních odkazů udělá absolutní URL a odstraní duplicity. Vrátí slovník, kde klíče jsou kódy obcí a hodnoty příslušné url.
    """
    odkazy_obce = {}

    for i in odkazy:
        abs_url = urllib.parse.urljoin(zaklad, i)
        query_cast = urllib.parse.parse_qs(urllib.parse.urlparse(abs_url).query) 
        #rozparsuje url, vybere query část a převede na slovník {'xobec': ['12345'], 'xokrsek': ['0']}
        xobec = query_cast.get("xobec", [""])[0].strip() #vytáhne konkrétní parametr xobec

        if xobec:
            # pokud daná obec v seznamu již je, nic se nestane, pokud ne - přidá se
            if xobec not in odkazy_obce:
                odkazy_obce[xobec] = abs_url

    return odkazy_obce

def ziskej_seznam_obci(html_kod):
    """
    Z tabulky na hlavní stránce načte kódy a názvy obcí.
    Vrací list slovníků ve tvaru {"kod_obce": ..., "nazev_obce": ...}.
    """
    obce = []

    for tr in html_kod.select("table tr"): # vybere všechny <tr> objekty uvnitř <table>
        tds = tr.find_all("td") # a v nich všechny <td> "řádky"
        if len(tds) < 2: # vyfiltruje hlavičku a prázdné řádky - pokud je řádků méně než 2 jedná se o popisky
            continue  

        a = tds[0].find("a")              # na první pozici najde tag <a>
        if not a:
            continue
        kod = a.get_text()      # vyfiltrure text tagu <a>
        nazev = tds[1].get_text() # na druhé pozici vyfiltruje text

        obce.append({"kod_obce": kod, "nazev_obce": nazev})
    return obce

def vycisti_text(text):
    """
    Vytáhne a ořízne text. Při None vrací prázdný řetězec.
    """
    if text is None:
        return ""
    return text.get_text().strip()

def najdi_data(prvek, selector, pozice = -1):
    """
    Najde všechny shody (selector) uvnitř prvku a vrátí text buňky na zadané pozici.
    """
    if prvek is None:
        return None
    data = prvek.select(selector)
    if not data:
        return None
    return vycisti_text(data[pozice])

def zpracuj_detail_obce_souhrn(html_kod_obce, tabulka):
    """
    Z tabulky získá souhrnná čísla pro konkrétní obec: Voliči v seznamu, Vydané obálky, Odevzdané obálky, Platné hlasy. 
    """
    t1 = html_kod_obce.find("table", id=tabulka) # najdu tabulku s daným ID

    return {
        "Voliči v seznamu": najdi_data(t1, 'td[headers="sa2"]', -1),
        "Vydané obálky":    najdi_data(t1, 'td[headers="sa3"]', -1),
        "Odevzdané obálky": najdi_data(t1, 'td[headers="sa5"]', -1),
        "Platné hlasy":     najdi_data(t1, 'td[headers="sa6"]', -1),
    }

def zpracuj_detail_obce_strany(html_kod_obce):
    """
    Vezmeme všechny tabulky s class="table" kromě ps311_t1 (tabulkla souhrnu) a z každého datového
    řádku vytáhneme název strany (2. sloupec) a hlasy (3. sloupec) a uloží do výsledků.
    """
    vysledky = {}
    tables = html_kod_obce.find_all("table", {"class": "table"})

    for t in tables:
        if t.get("id") == "ps311_t1":
            continue  # přeskočí souhrnou tabulku

        for tr in t.find_all("tr"):
            # použijeme najdi_data na konkrétní řádek:
            nazev = najdi_data(tr, 'td[headers$="sb2"]', 0)    
            hlasy = najdi_data(tr, 'td[headers$="sb3"]', 0)

            # přeskočí prázdné řádky a řádky tvořené pomlčkou
            if not nazev or nazev.strip() == "-":
                continue

            vysledky[nazev] = hlasy

    return vysledky

def main():
    """
    Hlavní běh skriptu: načte argumenty, posbírá data za okres, složí tabulku a uloží CSV.
    Vypíše souhrnné počty a název výstupního souboru.
    """
    url = sys.argv[1]
    vystup = sys.argv[2]
    
    html_kod = overeni_argumentu(zaklad_url, url, vystup)
    odkazy_vsechny = ziskej_odkazy_z_main(html_kod)
    odkazy_obce = odstraneni_duplicit(odkazy_vsechny, zaklad = zaklad_url)
    seznam_obce = ziskej_seznam_obci(html_kod)

    print(f"Počet nalezených href: {len(odkazy_vsechny)}")
    print(f"Počet unikátních obcí (odkazy_obce): {len(odkazy_obce)}")
    print(f"Počet obcí v tabulce (seznam_obce): {len(seznam_obce)}")

    vsechny_strany = set()
    radky = []

    for obec in seznam_obce:
        kod = obec["kod_obce"]
        detail_url = odkazy_obce.get(kod)
        if not detail_url:
            continue

        html_kod_obce = stahni_html(detail_url)
        if not html_kod_obce:
            continue

        souhrn = zpracuj_detail_obce_souhrn(html_kod_obce, "ps311_t1")
        if not souhrn:
            continue

        strany = zpracuj_detail_obce_strany(html_kod_obce)
        vsechny_strany.update(strany.keys())

        radek = {"Kód obce": kod, "Název obce": obec["nazev_obce"]} | souhrn | strany # sjednocení slovníků pomocí operátoru |
        radky.append(radek)

    if not radky:
        print("Nebyl získán žádný výsledek – zkontroluj prosím vstupní URL.")
        sys.exit(1)

    locale.setlocale(locale.LC_COLLATE, "Czech") 

    pevne = ["Kód obce", "Název obce", "Voliči v seznamu", "Vydané obálky", "Odevzdané obálky", "Platné hlasy"]
    # s využitím locale modulu, který pro třídění použije česká pravidla (při seřazení nebudou strany začínající písmeny s háčky na konci)
    strany_sloupce = sorted(vsechny_strany, key=lambda s: locale.strxfrm(s.lower()))
    hlavicka = pevne + strany_sloupce

    # upozorní, pokud soubor je již vytvořený a otevřený
    try:
     with open(vystup, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=hlavicka, delimiter=";")
        w.writeheader()
        w.writerows(radky)
    except PermissionError:
        print(f"Soubor '{vystup}' je otevřený. Zavři ho nebo zvol jiné jméno.")
        sys.exit(1)

    print(f"Hotovo! Uloženo {len(radky)} obcí do '{vystup}'. Sloupců stran: {len(strany_sloupce)}")

if __name__ == "__main__":
    main()