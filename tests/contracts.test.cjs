'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Ajv2020 = require('ajv/dist/2020');
const addFormats = require('ajv-formats');
const { loadSchema, schemaNames, version } = require('../index.cjs');
const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);
const validators = Object.fromEntries(schemaNames.map(name => [name, ajv.compile(loadSchema(name))]));
const manifest = require('../examples/manifest.json');
for (const fixture of manifest) {
  test(fixture.path, () => {
    const value = JSON.parse(fs.readFileSync(path.join(__dirname, '../examples', fixture.path), 'utf8'));
    assert.equal(validators[fixture.schema](value), fixture.valid);
  });
}
test('loader rejects paths and returns independent documents', () => {
  assert.throws(() => loadSchema('../package'), RangeError);
  const first = loadSchema('error');
  first.title = 'mutated';
  assert.notEqual(loadSchema('error').title, 'mutated');
  assert.equal(version, require('../package.json').version);
});
