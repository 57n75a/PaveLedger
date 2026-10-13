// Regenerates public/schemas/contract-import.schema.json and docs/CONTRACT_IMPORT.md from lib/contract-schema.ts.
// Run: node --experimental-strip-types scripts/build-import-schema.mjs
import fs from 'node:fs';
import {CONTRACT_SCHEMA, MAX_IMPORT_ROWS, COUNTRIES} from '../lib/contract-schema.ts';
const prop = f => {
  const base = {title: f.label, description: f.help, examples: [f.example]};
  switch (f.type) {
    case 'date': return {...base, type: 'string', pattern: '^(\\d{4}-\\d{1,2}-\\d{1,2}|\\d{1,2}\\.\\s?\\d{1,2}\\.\\s?\\d{4}\\.?)$', description: f.help + ' YYYY-MM-DD or DD.MM.YYYY.'};
    case 'email': return {...base, type: 'string', format: 'email', maxLength: f.max};
    case 'phone': return {...base, type: 'string', pattern: '^[+\\d\\s().\\-/]{5,40}$'};
    case 'number': return {...base, type: ['number', 'string'], minimum: f.min, maximum: f.max};
    case 'country': return {...base, type: 'string', description: f.help + ' ' + COUNTRIES.join(', ') + ' (also accepts Srbija, Serbia, RS, Europe, Canada).'};
    case 'list': return {...base, oneOf: [{type: 'string', maxLength: f.max, description: 'Separated by ; or new lines'}, {type: 'array', items: {type: 'string'}}]};
    default: return {...base, type: 'string', maxLength: f.max};
  }
};
const schema = {
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  $id: 'https://paveledger.vercel.app/schemas/contract-import.schema.json',
  title: 'PaveLedger contract import',
  description: `One object per contractor contract. Up to ${MAX_IMPORT_ROWS} rows per import. The same field names are used as CSV/Excel headers and XML element names. Rows matching an existing contract on firm, road, start and end are skipped as duplicates.`,
  type: 'array', maxItems: MAX_IMPORT_ROWS,
  items: {type: 'object', additionalProperties: true, required: CONTRACT_SCHEMA.filter(f => f.required).map(f => f.key),
    properties: Object.fromEntries(CONTRACT_SCHEMA.map(f => [f.key, prop(f)])),
    dependentRequired: {scopeLat: ['scopeLng', 'scopeRadius'], scopeLng: ['scopeLat', 'scopeRadius'], scopeRadius: ['scopeLat', 'scopeLng']}},
};
fs.writeFileSync('public/schemas/contract-import.schema.json', JSON.stringify(schema, null, 2) + '\n');
const md = `# Contract import schema

Contractor firms in PaveLedger are defined by their contracts, so contractors are imported as contracts: one row (or XML element, or JSON object) per contract. This file is generated from \`lib/contract-schema.ts\` by \`scripts/build-import-schema.mjs\`; the import screen and the server use the same rules.

- Formats: Excel (XLSX, XLS), CSV (UTF-8), XML. Templates: Contracts → Import contracts → Import schema and guidelines, or Help and FAQ.
- Machine-readable schema: [\`/schemas/contract-import.schema.json\`](../public/schemas/contract-import.schema.json) (JSON Schema 2020-12).
- Up to ${MAX_IMPORT_ROWS} rows per import. Header names are matched automatically, including common Serbian headers.

| Column | Required | Field | Format | Example | Notes |
|---|---|---|---|---|---|
${CONTRACT_SCHEMA.map(f => `| \`${f.key}\` | ${f.required ? 'Yes' : 'No'} | ${f.label} | ${f.format} | ${f.example} | ${f.help} |`).join('\n')}

## Rules

- Dates: \`YYYY-MM-DD\` or \`DD.MM.YYYY\`; Excel date cells are accepted. Slashes are rejected because they are ambiguous. \`end\` cannot be before \`start\`.
- \`additionalRoads\`: street names separated by \`;\` or new lines.
- Map area: \`scopeLat\`, \`scopeLng\` and \`scopeRadius\` must be given together; radius 50–50,000 m.
- \`addressCountry\`: ${COUNTRIES.join(', ')}; Srbija, Serbia, RS, Europe and Canada are also understood.
- Duplicates: same \`contractor\`, \`road\`, \`start\` and \`end\` as an existing contract or an earlier row (ignoring case and accents) are skipped.
- Invalid rows are shown with the reason and are not imported; valid rows can be imported on their own.

## XML example

\`\`\`xml
<contracts>
  <contract>
${CONTRACT_SCHEMA.filter(f => f.required).map(f => `    <${f.key}>${f.example}</${f.key}>`).join('\n')}
  </contract>
</contracts>
\`\`\`
`;
fs.writeFileSync('docs/CONTRACT_IMPORT.md', md);
console.log('wrote public/schemas/contract-import.schema.json and docs/CONTRACT_IMPORT.md');
