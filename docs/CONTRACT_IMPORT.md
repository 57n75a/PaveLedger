# Contract import schema

Contractor firms in PaveLedger are defined by their contracts, so contractors are imported as contracts: one row (or XML element, or JSON object) per contract. This file is generated from `lib/contract-schema.ts` by `scripts/build-import-schema.mjs`; the import screen and the server use the same rules.

- Formats: Excel (XLSX, XLS), CSV (UTF-8), XML. Templates: Contracts → Import contracts → Import schema and guidelines, or Help and FAQ.
- Machine-readable schema: [`/schemas/contract-import.schema.json`](../public/schemas/contract-import.schema.json) (JSON Schema 2020-12).
- Up to 200 rows per import. Header names are matched automatically, including common Serbian headers.

| Column | Required | Field | Format | Example | Notes |
|---|---|---|---|---|---|
| `contractor` | Yes | Contractor firm | Text, up to 120 characters | Putevi Užice d.o.o. | Registered name of the firm. Use the same spelling every time so its contracts group together. |
| `road` | Yes | Road name | Text, up to 120 characters | Kralja Petra I | Main street or road the warranty covers, spelled exactly as in tickets. |
| `start` | Yes | Warranty begins | YYYY-MM-DD or DD.MM.YYYY | 2026-03-01 | First day of the warranty period. |
| `end` | Yes | Warranty ends | YYYY-MM-DD or DD.MM.YYYY, not before the start | 2028-03-01 | Last day of the warranty period. |
| `poc` | Yes | Point of contact | Text, up to 120 characters | Marko Petrović | Person at the firm who receives repair notices. |
| `email` | Yes | Contact email | A valid email address | marko@putevi-uzice.rs | Where repair notices are sent. Check it carefully. |
| `phone` | No | Phone number | Digits, spaces, +, -, ( ), up to 40 characters | +381 31 123 456 | Phone for urgent coordination. |
| `scope` | No | Work scope | Text, up to 2,000 characters | Kolovoz od raskrsnice sa ul. Omladinska do mosta, obe trake | What the warranty covers on that road, such as a section, lanes or chainage. |
| `additionalRoads` | No | Additional streets | Street names separated by ; or new lines | Vuka Karadžića; Dušanova | Other streets covered by the same contract. |
| `address` | No | Firm address | Text, up to 300 characters | Nikole Pašića 12, Užice | Postal address of the firm. |
| `addressCountry` | No | Country or region | SRB, EU, USA or CAN | SRB | Country of the firm address. Leave empty if unknown. |
| `notes` | No | Notes | Text, up to 4,000 characters | Ugovor br. 404-17/2026 | Internal notes, such as the contract number. |
| `scopeLat` | No | Area latitude | Decimal degrees, -90 to 90 | 43.8563 | Centre of the covered area on the map. Use together with longitude and radius. |
| `scopeLng` | No | Area longitude | Decimal degrees, -180 to 180 | 19.8487 | Centre of the covered area on the map. |
| `scopeRadius` | No | Area radius (m) | Whole metres, 50 to 50,000 | 500 | Radius around the centre. Tickets inside it are matched to this contract. |

## Rules

- Dates: `YYYY-MM-DD` or `DD.MM.YYYY`; Excel date cells are accepted. Slashes are rejected because they are ambiguous. `end` cannot be before `start`.
- `additionalRoads`: street names separated by `;` or new lines.
- Map area: `scopeLat`, `scopeLng` and `scopeRadius` must be given together; radius 50–50,000 m.
- `addressCountry`: SRB, EU, USA, CAN; Srbija, Serbia, RS, Europe and Canada are also understood.
- Duplicates: same `contractor`, `road`, `start` and `end` as an existing contract or an earlier row (ignoring case and accents) are skipped.
- Invalid rows are shown with the reason and are not imported; valid rows can be imported on their own.

## XML example

```xml
<contracts>
  <contract>
    <contractor>Putevi Užice d.o.o.</contractor>
    <road>Kralja Petra I</road>
    <start>2026-03-01</start>
    <end>2028-03-01</end>
    <poc>Marko Petrović</poc>
    <email>marko@putevi-uzice.rs</email>
  </contract>
</contracts>
```
