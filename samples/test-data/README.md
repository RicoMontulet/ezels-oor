# Audio-testdata

Deze map bevat drie korte clips uit de `test-clean`-split van LibriSpeech en één daarvan afgeleid multi-speakerbestand. De volledige set is kleiner dan 600 kB.

## Bestanden

- `1320-122617-0022.flac`: één spreker, 3,855 seconden.
- `260-123286-0000.flac`: één spreker, 7,040 seconden.
- `7729-102255-0039.flac`: één spreker, 6,815 seconden.
- `multi-speaker-sequence.flac`: bovenstaande clips achter elkaar, drie speakersegmenten, 17,710 seconden.
- `*.expected.json`: verwachte transcriptie, speakerlabels en tijden per gelijknamig audiobestand.

De drie teksten vormen samen geen natuurlijk gesprek. Het samengestelde bestand is alleen bedoeld als kleine technische test voor transcriptie en speaker diarization.

## Herkomst en licentie

De bronclips komen uit [LibriSpeech ASR corpus (OpenSLR SLR12)](https://www.openslr.org/12), via de [Hugging Face-datasetviewer](https://huggingface.co/datasets/openslr/librispeech_asr). LibriSpeech is samengesteld door Vassil Panayotov, Guoguo Chen, Daniel Povey en Sanjeev Khudanpur uit LibriVox-audioboeken.

LibriSpeech wordt verspreid onder de [Creative Commons Attribution 4.0 International-licentie](https://creativecommons.org/licenses/by/4.0/). Het samengestelde bestand is uitsluitend een concatenatie van de drie genoemde bronclips en valt onder dezelfde licentie.

## Verwachte uitvoer

Ieder `.expected.json`-bestand volgt het `TranscribeResult`-schema van de Azure Speech Fast Transcription API `2025-10-15`. De fixtures gebruiken de velden `durationMilliseconds`, `combinedPhrases` en `phrases`. Iedere phrase bevat `offsetMilliseconds`, `durationMilliseconds`, `text`, `locale` en een `speaker`-testlabel.

De speakerlabels zijn lokale verwachte labels. Azure kent speakergetallen per transcriptie zonder vaste volgorde toe; vergelijk diarization daarom op consistente sprekerwissels en niet op exacte nummers. `mai-transcribe-1` ondersteunt momenteel geen diarization en zal geen `speaker`-velden teruggeven. Gebruik een Azure Speech-model met diarization om alle fixturevelden te vergelijken.

De referentietranscripten komen uit LibriSpeech. Segmenttijden van het samengestelde bestand zijn gebaseerd op de grenzen tussen de bronclips; er zijn geen confidencewaarden of woordtimestamps toegevoegd.
