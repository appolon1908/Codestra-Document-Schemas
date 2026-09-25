'use strict';
const fs = require('node:fs');
const path = require('node:path');
const schemaNames = Object.freeze(['extraction-envelope', 'do-driver-licence',
  'reviewed-result', 'client-intake', 'error', 'worker-contract']);
function loadSchema(name) {
  if (!schemaNames.includes(name)) throw new RangeError(`Unknown schema: ${name}`);
  return JSON.parse(fs.readFileSync(path.join(__dirname, 'codestra_document_schemas',
    'schemas', 'v1', `${name}.schema.json`), 'utf8'));
}
module.exports = { version: '1.0.0', schemaNames, loadSchema };
