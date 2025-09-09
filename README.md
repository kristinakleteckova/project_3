# Projekt: Elections Scraper

Tento skript stáhne z volby.cz seznam obcí pro vybraný okres, pro každou obec otevře detail a vytáhne:
- souhrnná čísla (Voliči v seznamu, Vydané obálky, Odevzdané obálky, Platné hlasy),
- hlasy pro jednotlivé strany 

Výstupem bude **csv** soubor, obsahující 4 souhrnné sloupce dané obce a sloupce pro hlasy jednotlivých stran, ty budou seřazeny podle abecedy.

## Instalace knihoven
Ideálně použít **virtuální prostředí** vytvořené jen pro tento skript.
Součástí depozitáře je soubor requirements.txt obsahující soupis všech potřebných externích knihoven pro spuštění daného skriptu. 

### pro Windows:
cd "C:\Users\Ja\Projekt"
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt

### pro linux/macOS
cd "C:\Users\Ja\Projekt"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## Spuštění
Skript očekává 2 argumenty:
- URL na stránku „Výběr obce“ pro konkrétní okres (tj. odkaz ve sloupci X; URL má tvar ps32?...),
- název výstupního CSV ve tvaru vysledky_okres.csv.

## Přklad - okres Benešov
Spuštění skriptu: python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2101" vysledky_benesov.csv

Kód obce;Název obce;Voliči v seznamu;Vydané obálky;Odevzdané obálky;Platné hlasy;ANO 2011
529303;Benešov;13 104;8 485;8 476;8 437;2 577
532568;Bernartice;191;148;148;148;39
530743;Bílkovice;170;121;121;118;47

Pozn.: Pokud je výstupní CSV otevřené v Excelu, Windows nepovolí přepis a skript skončí chybou PermissionError. Stačí soubor zavřít a spustit skript znovu.





