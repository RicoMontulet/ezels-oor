# Audio-testdata

Deze map bevat drie korte clips uit de `test-clean`-split van LibriSpeech en één daarvan afgeleid multi-speakerbestand. De volledige set is kleiner dan 600 kB.

## Bestanden

- `1320-122617-0022.flac`: één spreker, 3,855 seconden.
- `260-123286-0000.flac`: één spreker, 7,040 seconden.
- `7729-102255-0039.flac`: één spreker, 6,815 seconden.
- `multi-speaker-sequence.flac`: bovenstaande clips achter elkaar, drie speakersegmenten, 17,710 seconden.
- `manifest.json`: verwachte transcriptie, speakerlabels, tijden en herkomst.

De drie teksten vormen samen geen natuurlijk gesprek. Het samengestelde bestand is alleen bedoeld als kleine technische test voor transcriptie en speaker diarization.

## Herkomst en licentie

De bronclips komen uit [LibriSpeech ASR corpus (OpenSLR SLR12)](https://www.openslr.org/12), via de [Hugging Face-datasetviewer](https://huggingface.co/datasets/openslr/librispeech_asr). LibriSpeech is samengesteld door Vassil Panayotov, Guoguo Chen, Daniel Povey en Sanjeev Khudanpur uit LibriVox-audioboeken.

LibriSpeech wordt verspreid onder de [Creative Commons Attribution 4.0 International-licentie](https://creativecommons.org/licenses/by/4.0/). Het samengestelde bestand is uitsluitend een concatenatie van de drie genoemde bronclips en valt onder dezelfde licentie.

## Verwachte data

`manifest.json` bevat referentietranscripten uit LibriSpeech. Speaker-ID's zijn anonieme corpuslabels, geen namen. Segmenttijden van het samengestelde bestand zijn gebaseerd op de grenzen tussen de bronclips; er zijn geen woordtimestamps toegevoegd.
