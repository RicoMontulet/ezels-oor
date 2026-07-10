# EzelsOor



EzelsOor is een hackathonproject voor het opnemen, transcriberen en samenvatten van gesprekken.



Een Raspberry Pi neemt audio op via een aangesloten microfoon. De audio wordt verwerkt met diensten in Azure AI Foundry. De oplossing herkent verschillende sprekers, zet gesproken tekst om naar geschreven tekst en genereert met een taalmodel een samenvatting.



## Doel van de hackathon



Aan het einde van de hackathon willen we een werkende demonstratie waarin:



1. een gesprek via de Raspberry Pi wordt opgenomen;

2. de opname naar Azure wordt verstuurd;

3. de gesproken tekst wordt getranscribeerd;

4. verschillende sprekers herkenbaar zijn;

5. een samenvatting en eventuele actiepunten worden gegenereerd;

6. het resultaat zichtbaar of opvraagbaar is.



De nadruk ligt op een werkende end-to-end ervaring. De oplossing hoeft niet production-ready te zijn.



## Werkgebieden



* `device/`: audio-opname en communicatie vanaf de Raspberry Pi.

* `backend/`: verwerking, transcriptie, sprekerherkenning en samenvatting.

* `frontend/`: bediening en presentatie van resultaten.

* `infra/`: Azure-configuratie en deployment.

* `shared/contracts/`: gedeelde interfaces en datamodellen.

* `docs/`: gezamenlijke technische afspraken.

* `samples/`: voorbeelddata.



De mappenstructuur is een richtlijn. Teams mogen hiervan afwijken wanneer dit de voortgang helpt, zolang gedeelde interfaces en instructies duidelijk blijven.



## Uitgangspunten



* Houd oplossingen zo eenvoudig mogelijk.

* Optimaliseer voor een werkende demo.

* Leg alleen beslissingen vast die andere teams beïnvloeden.

* Voeg geen secrets, sleutels of persoonsgegevens toe aan de repository.

* Gebruik voorbeelddata zonder vertrouwelijke informatie.

* Bespreek wijzigingen aan gedeelde contracten met de betrokken teams.



## Samenwerken



Werk in korte feature branches en maak kleine pull requests. Directe afstemming heeft tijdens de hackathon voorrang op uitgebreide documentatie.



### Aan de slag



Kies eerst een korte, herkenbare teamnaam. Gebruik kleine letters en koppeltekens, bijvoorbeeld `team-audio`.



Clone daarna de publieke repository:



```bash
git clone https://github.com/RicoMontulet/ezels-oor.git
cd ezels-oor
```



Maak een eigen branch met de teamnaam. Werk niet rechtstreeks op `main`:



```bash
git switch -c team/<teamnaam>
git push -u origin team/<teamnaam>
```



Werk vanaf deze branch en commit kleine, samenhangende wijzigingen:



```bash
git add <bestanden>
git commit -m "<korte beschrijving>"
git push
```



Open een pull request naar `main` zodra een wijziging gedeeld of geïntegreerd kan worden.



Iedere map bevat indien nodig een eigen README met:



* het doel van het onderdeel;

* hoe het lokaal gestart wordt;

* benodigde configuratie;

* input en output;

* bekende beperkingen.



## Definition of done



Een onderdeel is klaar voor de demo wanneer:



* het geïntegreerd kan worden met de andere onderdelen;

* de benodigde configuratie beschreven is;

* fouten voldoende zichtbaar zijn om problemen tijdens de demo te onderzoeken;

* er geen secrets of gevoelige opnames in de repository staan.
