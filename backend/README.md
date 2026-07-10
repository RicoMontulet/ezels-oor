# Backend

Dit werkgebied bevat straks de verwerking van opnames met Azure AI Foundry en de API voor resultaten.

## Verantwoordelijkheden

- opnames ontvangen en valideren;
- audiobestanden transcriberen en sprekers onderscheiden;
- samenvatting, afspraken en actiepunten genereren;
- status, resultaten en fouten beschikbaar maken.

## Verwachte koppeling

- **Input:** audiobestand en metadata volgens `shared/contracts/`.
- **Output:** transcriptsegmenten met sprekers, samenvatting, afspraken en actiepunten.
- **Configuratie:** Azure-endpoints, deploymentnamen en secrets via omgevingsvariabelen.

## Lokaal starten

Nog niet beschikbaar. Keuze van runtime en startcommando volgt tijdens de hackathon.

## Bekende beperkingen

Servicekeuzes, maximale opnameduur en foutafhandeling zijn nog niet vastgesteld.
