"""Synthetic contract cases shared by both validator implementations."""
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'examples'
COMMON = dict(scan_id='scan-synthetic-001', tenant_id='tenant-example', schema_version='1.0.0')
DIGEST = 'sha256:' + 'a' * 64
HASH = 'hmac-sha256:' + 'b' * 64
TIME = '2026-09-25T12:00:00Z'
FIELDS = dict(full_name='PERSONA SINTETICA EJEMPLO', document_number='000-0000000-0',
    address='CALLE FICTICIA 123, CIUDAD EJEMPLO', height=1.7, weight_lb=150,
    sex='F', blood_type='O+', birth_date='1990-01-15', issue_date='2024-01-15',
    expiry_date='2028-01-15', category='02', restriction='NINGUNA',
    first_issue_date='2010-01-15', card_serial='SYNTHETIC-001')
EXTRACTION = dict(**COMMON, document_type='driver_license', country='DO',
    engine=dict(name='synthetic-ocr', version='0.0.0'), fields=FIELDS,
    field_evidence={'document_number': [dict(source='ocr', confidence=0.98, page=1,
        bbox=[0.1, 0.1, 0.4, 0.2], raw_text='000-0000000-0')]},
    warnings=[], qr_evidence=dict(status='decoded', payload_digest=DIGEST, raw_payload='SYNTHETIC-QR'),
    content_digests=[dict(role='front', digest=DIGEST)])
REVIEWED = dict(**COMMON, country='DO', document_type='driver_license', status='confirmed',
    document_hash=HASH, document_hash_key_id='synthetic-key-v1', document_last4='0000',
    fields={k: v for k, v in FIELDS.items() if k != 'document_number'},
    review=dict(reviewer_id='reviewer-example', reviewed_at=TIME, method='human'))
INTAKE = {k: REVIEWED[k] for k in [*COMMON, 'country', 'document_type', 'document_hash',
    'document_hash_key_id', 'document_last4']}
INTAKE.update(full_name=FIELDS['full_name'], reviewed_at=TIME)
ERROR = dict(**COMMON, code='EXTRACTION_FAILED', stage='extract', retryable=False, occurred_at=TIME)
MESSAGE = dict(**COMMON, job_id='job-example', attempt=1, sent_at=TIME)
REQUEST = dict(**MESSAGE, kind='extract.request', document_type='driver_license', country='DO',
    inputs=[dict(asset_id='asset-example', side='front', media_type='image/png', digest=DIGEST)],
    deadline_at='2026-09-25T12:05:00Z')
SUCCESS = dict(**MESSAGE, kind='extract.succeeded', result=EXTRACTION)
FAILURE = dict(**MESSAGE, kind='extract.failed', error=ERROR)
CASES = []


def case(name, schema, value, valid=True):
    path = ('valid/' if valid else 'invalid/') + name + '.json'
    (ROOT / path).write_text(json.dumps(value, indent=2) + '\n')
    CASES.append(dict(path=path, schema=schema, valid=valid))


def change(base, path, value=None, remove=False):
    result = deepcopy(base)
    parent = result
    for key in path[:-1]:
        parent = parent[key]
    if remove:
        del parent[path[-1]]
    else:
        parent[path[-1]] = value
    return result


def bad(name, schema, base, path, value=None, remove=False):
    case(name, schema, change(base, path, value, remove), False)


def build():
    for name, value in [('extraction-envelope', EXTRACTION), ('do-driver-licence', EXTRACTION),
                        ('reviewed-result', REVIEWED), ('client-intake', INTAKE), ('error', ERROR)]:
        case(name, name, value)
        bad(name + '-unknown-property', name, value, ['unexpected'], 'forbidden')
        bad(name + '-wrong-version', name, value, ['schema_version'], '2.0.0')
        bad(name + '-missing-tenant', name, value, ['tenant_id'], remove=True)
    for name, value in [('request', REQUEST), ('success', SUCCESS), ('failure', FAILURE)]:
        case('worker-' + name, 'worker-contract', value)
        bad('worker-' + name + '-unknown', 'worker-contract', value, ['unknown'], True)
    case('licence-all-unknown', 'do-driver-licence', change(EXTRACTION, ['fields'], {k: None for k in FIELDS}))
    case('licence-leap-date', 'do-driver-licence', change(EXTRACTION, ['fields', 'birth_date'], '2000-02-29'))
    case('generic-other-type', 'extraction-envelope', change(EXTRACTION, ['document_type'], 'invoice'))
    case('qr-not-detected', 'do-driver-licence', change(EXTRACTION, ['qr_evidence'], {'status': 'not_detected'}))
    case('intake-optional-fields', 'client-intake', {**INTAKE, 'birth_date': None, 'address': None})
    mutations = [
        ('invalid-calendar', ['fields', 'birth_date'], '2023-02-29'),
        ('invalid-date-shape', ['fields', 'issue_date'], '25/09/2026'),
        ('number-regex', ['fields', 'document_number'], 'abc'),
        ('number-type', ['fields', 'document_number'], 12345678901),
        ('height-unit', ['fields', 'height'], 170),
        ('weight-negative', ['fields', 'weight_lb'], -10),
        ('sex-enum', ['fields', 'sex'], 'unknown'),
        ('blood-enum', ['fields', 'blood_type'], 'C+'),
        ('name-blank', ['fields', 'full_name'], '   '),
        ('name-long', ['fields', 'full_name'], 'A' * 201),
        ('serial-regex', ['fields', 'card_serial'], 'bad serial'),
        ('category-regex', ['fields', 'category'], '💥'),
        ('field-unknown', ['fields', 'portrait'], 'base64'),
        ('wrong-country', ['country'], 'US'),
        ('wrong-document', ['document_type'], 'passport'),
        ('evidence-unknown', ['field_evidence', 'unknown'], []),
        ('confidence-range', ['field_evidence', 'document_number', 0, 'confidence'], 1.1),
        ('bbox-range', ['field_evidence', 'document_number', 0, 'bbox'], [0, 0, 2, 1]),
        ('bbox-length', ['field_evidence', 'document_number', 0, 'bbox'], [0, 1]),
        ('evidence-extra', ['field_evidence', 'document_number', 0, 'image'], 'base64'),
        ('qr-status', ['qr_evidence', 'status'], 'unreadable'),
        ('qr-extra', ['qr_evidence', 'image'], 'base64'),
        ('digest-regex', ['content_digests', 0, 'digest'], 'sha256:bad'),
        ('digests-empty', ['content_digests'], []),
        ('warning-payload', ['warnings'], [{'code': 'MISSING_FIELD', 'severity': 'warning', 'message': 'secret'}]),
        ('engine-extra', ['engine', 'api_key'], 'secret'),
    ]
    for name, path, value in mutations:
        bad(name, 'do-driver-licence', EXTRACTION, path, value)
    bad('missing-licence-field', 'do-driver-licence', EXTRACTION, ['fields', 'expiry_date'], remove=True)
    bad('qr-missing-digest', 'do-driver-licence', EXTRACTION, ['qr_evidence', 'payload_digest'], remove=True)
    for schema, value in [('reviewed-result', REVIEWED), ('client-intake', INTAKE)]:
        for key in ['document_number', 'raw_image', 'biometric_payload', 'qr_evidence', 'field_evidence']:
            bad(schema + '-reject-' + key, schema, value, [key], '000-0000000-0')
        bad(schema + '-hash-required', schema, value, ['document_hash'], remove=True)
        bad(schema + '-last4-required', schema, value, ['document_last4'], remove=True)
        bad(schema + '-last4-regex', schema, value, ['document_last4'], '00000')
        bad(schema + '-hash-regex', schema, value, ['document_hash'], DIGEST)
    bad('reviewed-nested-number', 'reviewed-result', REVIEWED, ['fields', 'document_number'], FIELDS['document_number'])
    bad('reviewed-null-name', 'reviewed-result', REVIEWED, ['fields', 'full_name'], None)
    bad('reviewed-not-confirmed', 'reviewed-result', REVIEWED, ['status'], 'pending')
    bad('reviewed-freeform-note', 'reviewed-result', REVIEWED, ['review', 'note'], 'secret')
    bad('reviewed-invalid-timestamp', 'reviewed-result', REVIEWED, ['review', 'reviewed_at'], '2026-02-30T12:00:00Z')
    bad('intake-invalid-birth', 'client-intake', INTAKE, ['birth_date'], '2025-02-29')
    bad('generic-nested-payload', 'extraction-envelope', EXTRACTION, ['fields', 'nested'], {'image': 'base64'})
    bad('generic-country-length', 'extraction-envelope', EXTRACTION, ['country'], 'DOM')
    bad('error-raw-message', 'error', ERROR, ['message'], 'sensitive exception')
    bad('error-unknown-code', 'error', ERROR, ['code'], 'OTHER')
    bad('error-retry-type', 'error', ERROR, ['retryable'], 'false')
    bad('worker-result-error-exclusive', 'worker-contract', SUCCESS, ['error'], ERROR)
    bad('worker-success-missing-result', 'worker-contract', SUCCESS, ['result'], remove=True)
    bad('worker-empty-inputs', 'worker-contract', REQUEST, ['inputs'], [])
    bad('worker-negative-attempt', 'worker-contract', REQUEST, ['attempt'], 0)
    bad('worker-signed-url', 'worker-contract', REQUEST, ['inputs', 0, 'url'], 'https://example.invalid/secret')
    bad('worker-wrong-profile', 'worker-contract', SUCCESS, ['result', 'country'], 'US')
    bad('worker-nested-error-message', 'worker-contract', FAILURE, ['error', 'message'], 'secret')
    (ROOT / 'manifest.json').write_text(json.dumps(CASES, indent=2) + '\n')

if __name__ == '__main__':
    build()
