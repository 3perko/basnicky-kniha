## Vstupy (čítaj IBA tieto 3 súbory, nič iné v repozitári)
- /home/user/basnicky-kniha/brief_kniha.md – zadanie knihy
- /home/user/basnicky-kniha/pravidla_z_pilotu.md – záväzné doplnky briefu
- {DAVKA} – aktuálna dávka básničiek na hodnotenie

Nečítaj iné súbory (staršie verzie, hodnotenia iných kritikov, plán). Hodnotíš nezávisle.

## Výstup
Pre KAŽDÚ básničku v dávke zvlášť uveď:
- skóre 1–10 (môžeš použiť desatiny),
- čo funguje,
- konkrétne a vykonateľné zmeny k 10/10 (číslo verša, problém, návrh riešenia). Môžeš navrhnúť aj úplne nový koncept alebo inú formu.

Pozn.: Pri hádankach je v knihe nadpis nahradený slovom „HÁDANKA“ a posledné rýmové slovo (riešenie) je vytlačené ako vynechávka „……“, ktorú dieťa doplní; riešenie je na konci knihy. V rukopise dávky je riešenie vypísané, aby sa dalo hodnotiť.

Celé hodnotenie zapíš po slovensky do súboru {VYSTUP} (Markdown). Na úplný koniec súboru pridaj strojovo čitateľný blok presne v tomto tvare:

```json
{"kritik": "{K}", "hodnotenia": [
  {"cislo": 1, "nazov": "NÁZOV", "skore": 7.5, "funguje": "1–2 vety", "zmenit": "najdôležitejšie zmeny k 10/10, 1–3 vety s číslami veršov"}
]}
```

Čísla „cislo“ zodpovedajú číslam básničiek v dávke. Po zapísaní súboru odpovedz iba krátkym zhrnutím: zoznam „číslo názov – skóre“.
