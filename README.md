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

## Azure API's

De configuratie in `.env.example` bevat drie afzonderlijke Azure-resources. Maak lokaal een `.env` op basis van dit bestand en vul alleen de drie API-sleutels in. Commit `.env` nooit.

```bash
cp .env.example .env
```

Laad de variabelen voor een lokale shell als volgt:

```bash
set -a
. ./.env
set +a
```

### Speech: audio naar transcript en sprekers

`SPEECH_ENDPOINT`, `SPEECH_REGION` en `SPEECH_API_KEY` horen bij Azure Speech. Voor deze demo is de synchronische Fast Transcription API gebruikt:

```text
POST $SPEECH_ENDPOINT/speechtotext/transcriptions:transcribe?api-version=2025-10-15
```

Stuur een `multipart/form-data`-request met een `audio`-bestand en een JSON-veld `definition`. Gebruik `locales` voor de spreektaal en zet `diarization.enabled` op `true` wanneer sprekerwissels nodig zijn. De response bevat:

* `combinedPhrases`: volledige leesbare transcriptie;
* `phrases`: segmenten met `offsetMilliseconds`, `durationMilliseconds`, tekst, confidence en een `speaker`;
* `words`: woordtijden binnen ieder segment.

Sprekerlabels zijn alleen stabiel binnen één request. Bewaar daarom eigen deelnemersnamen los van Azure-labels. Dit endpoint is basis voor opname, transcriptie en diarization in EzelsOor.

### Language: transcript analyseren

`LANGUAGE_ENDPOINT` en `LANGUAGE_API_KEY` horen bij Azure AI Language. Geef hier tekst door nadat Speech een transcript heeft gemaakt:

```text
POST $LANGUAGE_ENDPOINT/language/:analyze-text?api-version=2024-11-01
```

De body kiest één analyse met `kind`. Getest voor dit project: `SentimentAnalysis` (document- en zinsentiment, optioneel opinion mining) en `KeyPhraseExtraction`. De resource ondersteunt, afhankelijk van ingeschakelde Azure-functies en regio, ook onder meer taaldetectie, named-entity recognition, PII-detectie, extractive/abstractive summarization en Conversational Language Understanding. Gebruik dit endpoint voor samenvatting-voorbewerking, actiepuntdetectie en privacycontroles; valideer beschikbaarheid van niet-geteste functies eerst in Azure.

### Translator: transcript vertalen

`TRANSLATOR_ENDPOINT` en `TRANSLATOR_API_KEY` horen bij Azure AI Translator. Stuur een JSON-array met één of meer objecten met `Text` naar:

```text
POST $TRANSLATOR_ENDPOINT/translate?api-version=3.0&from=en&to=nl
```

Gebruik headers `Ocp-Apim-Subscription-Key`, `Ocp-Apim-Subscription-Region` (voor deze resource: `westeurope`) en `Content-Type: application/json; charset=utf-8`. De response bevat per invoertekst een `translations`-array met `text` en doelcode `to`. Vertaal pas na transcriptie; timings en speakerlabels blijven in eigen applicatiedata naast vertaalde tekst staan.

Concrete requests, verwachte verschillen en vastgelegde testresponses staan in [`samples/test-data/README.md`](samples/test-data/README.md).



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
git switch -c <teamnaam>
git push -u origin <teamnaam>
```



Werk vanaf deze branch en commit kleine, samenhangende wijzigingen:



```bash
git add <bestanden>
git commit -m "<korte beschrijving>"
git push
```



Open een pull request naar `main` zodra een wijziging gedeeld of geïntegreerd kan worden.

### Bijdragen zonder schrijftoegang (fork)

De repository is publiek. Iedereen kan bijdragen zonder schrijftoegang via een fork:

```bash
gh repo fork RicoMontulet/ezels-oor --clone
cd ezels-oor
git switch -c <korte-beschrijving-van-je-wijziging>
```

Werk vanaf deze branch, commit je wijzigingen en push naar je eigen fork:

```bash
git add <bestanden>
git commit -m "<korte beschrijving>"
git push -u origin <korte-beschrijving-van-je-wijziging>
```

Open daarna een pull request terug naar `RicoMontulet/ezels-oor`:

```bash
gh pr create --repo RicoMontulet/ezels-oor
```

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
