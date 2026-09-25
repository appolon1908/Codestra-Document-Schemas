"""Deterministically build standalone v1 schemas; no network or runtime configuration."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'codestra_document_schemas/schemas/v1'
BASE = 'https://schemas.codestra.dev/document-intelligence/v1/'


def obj(properties, required=None, **extra):
    return dict(type='object', properties=properties,
                required=list(properties) if required is None else required,
                additionalProperties=False, **extra)


def string(limit=128, pattern=r'\S'):
    return dict(type='string', minLength=1, maxLength=limit, pattern=pattern)


def ref(name):
    return {'$ref': '#/$defs/' + name}


def array(items, maximum=100):
    return dict(type='array', items=items, maxItems=maximum)


def nullable(schema):
    return {'anyOf': [schema, {'type': 'null'}]}


def enum(*values):
    return {'type': 'string', 'enum': list(values)}


DEFS = {
    'id': string(128, r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'),
    'date': dict(type='string', format='date', minLength=10, maxLength=10,
                 pattern=r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'),
    'timestamp': dict(type='string', format='date-time', maxLength=40,
                      pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$'),
    'digest': string(71, r'^sha256:[0-9a-f]{64}$'),
    'documentHash': string(76, r'^hmac-sha256:[0-9a-f]{64}$'),
    'last4': string(4, r'^[0-9]{4}$'),
    'confidence': dict(type='number', minimum=0, maximum=1),
    'engine': obj({'name': ref('id'), 'version': string(64, r'^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$')}),
    'warning': obj({'code': enum('LOW_CONFIDENCE', 'MISSING_FIELD', 'QR_UNREADABLE',
                                 'QR_MISMATCH', 'UNSUPPORTED_LAYOUT', 'DATE_ORDER', 'REVIEW_REQUIRED'),
                    'field': string(64, r'^[a-z][a-z0-9_]{0,63}$'),
                    'severity': enum('info', 'warning', 'error')}, ['code', 'severity']),
    'bbox': dict(type='array', minItems=4, maxItems=4,
                 items=dict(type='number', minimum=0, maximum=1),
                 description='Normalized [x_min, y_min, x_max, y_max]. Application checks ordering.'),
    'evidence': obj({'source': enum('ocr', 'qr', 'derived'), 'confidence': ref('confidence'),
                     'page': dict(type='integer', minimum=1, maximum=100), 'bbox': ref('bbox'),
                     'raw_text': string(2048)}, ['source', 'confidence']),
    'qr': {'oneOf': [
        obj({'status': {'const': 'decoded'}, 'payload_digest': ref('digest'),
             'raw_payload': string(8192)}, ['status', 'payload_digest']),
        obj({'status': enum('not_detected', 'unreadable')})]},
    'contentDigest': obj({'role': enum('front', 'back', 'document'), 'digest': ref('digest')}),
}
FIELDS = {
    'full_name': string(200),
    'document_number': dict(**string(13, r'^(?:[0-9]{11}|[0-9]{3}-[0-9]{7}-[0-9])$'),
                            description='Transient OCR only; never persist or log the clear value.'),
    'address': string(500),
    'height': dict(type='number', minimum=0.3, maximum=3, description='Normalized metres.'),
    'weight_lb': dict(type='number', minimum=1, maximum=1500),
    'sex': enum('M', 'F', 'X'),
    'blood_type': enum('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'),
    'birth_date': ref('date'), 'issue_date': ref('date'), 'expiry_date': ref('date'),
    'category': string(20, r'^[A-Z0-9][A-Z0-9 ./-]{0,19}$'),
    'restriction': string(200), 'first_issue_date': ref('date'),
    'card_serial': string(40, r'^[A-Za-z0-9][A-Za-z0-9-]{0,39}$'),
}
DEFS['licenceFields'] = obj({k: nullable(v) for k, v in FIELDS.items()})
DEFS['reviewedFields'] = obj({k: nullable(v) for k, v in FIELDS.items() if k != 'document_number'})
# A confirmed identity must have a name; other card fields may remain unknown.
DEFS['reviewedFields']['properties']['full_name'] = FIELDS['full_name']
DEFS['genericFields'] = dict(type='object', maxProperties=100,
    propertyNames=string(64, r'^[a-z][a-z0-9_]{0,63}$'),
    additionalProperties={'anyOf': [string(2048), {'type': 'number'}, {'type': 'boolean'}, {'type': 'null'}]})
DEFS['fieldEvidence'] = dict(type='object', maxProperties=100,
    propertyNames=string(64, r'^[a-z][a-z0-9_]{0,63}$'), additionalProperties=array(ref('evidence'), 20))
DEFS['licenceEvidence'] = obj({k: array(ref('evidence'), 20) for k in FIELDS}, [])
COMMON = {'scan_id': ref('id'), 'tenant_id': ref('id'), 'schema_version': {'const': '1.0.0'}}
EXTRACTION = obj({**COMMON, 'document_type': string(64, r'^[a-z][a-z0-9_]{0,63}$'),
    'country': string(2, r'^[A-Z]{2}$'), 'engine': ref('engine'), 'fields': ref('genericFields'),
    'field_evidence': ref('fieldEvidence'), 'warnings': array(ref('warning')),
    'qr_evidence': ref('qr'),
    'content_digests': {**array(ref('contentDigest'), 10), 'minItems': 1, 'uniqueItems': True}})
LICENCE = obj({**EXTRACTION['properties'], 'country': {'const': 'DO'},
    'document_type': {'const': 'driver_licence'}, 'fields': ref('licenceFields'),
    'field_evidence': ref('licenceEvidence')})
REVIEWED = obj({**COMMON, 'country': {'const': 'DO'}, 'document_type': {'const': 'driver_licence'},
    'status': {'const': 'confirmed'}, 'document_hash': ref('documentHash'),
    'document_hash_key_id': ref('id'), 'document_last4': ref('last4'),
    'fields': ref('reviewedFields'),
    'review': obj({'reviewer_id': ref('id'), 'reviewed_at': ref('timestamp'),
                   'method': enum('human', 'policy')})})
INTAKE = obj({**COMMON, 'country': {'const': 'DO'}, 'document_type': {'const': 'driver_licence'},
    'document_hash': ref('documentHash'), 'document_hash_key_id': ref('id'),
    'document_last4': ref('last4'), 'full_name': FIELDS['full_name'],
    'birth_date': nullable(ref('date')), 'address': nullable(FIELDS['address']),
    'reviewed_at': ref('timestamp')},
    [*COMMON, 'country', 'document_type', 'document_hash', 'document_hash_key_id',
     'document_last4', 'full_name', 'reviewed_at'])
ERROR = obj({**COMMON, 'code': enum('INVALID_INPUT', 'UNSUPPORTED_DOCUMENT', 'EXTRACTION_FAILED',
    'TIMEOUT', 'RATE_LIMITED', 'INTERNAL_ERROR'), 'stage': enum('ingest', 'extract', 'validate', 'review'),
    'retryable': {'type': 'boolean'}, 'occurred_at': ref('timestamp')})
DEFS['extraction'] = EXTRACTION
DEFS['error'] = ERROR
# v1 worker runs the supported DR profile, while the generic envelope remains reusable.
DEFS['licence'] = LICENCE
MESSAGE = {**COMMON, 'job_id': ref('id'), 'attempt': dict(type='integer', minimum=1, maximum=100),
           'sent_at': ref('timestamp')}
WORKER = {'oneOf': [
    obj({**MESSAGE, 'kind': {'const': 'extract.request'}, 'document_type': {'const': 'driver_licence'},
         'country': {'const': 'DO'}, 'inputs': {**array(obj({'asset_id': ref('id'),
             'side': enum('front', 'back'), 'media_type': enum('image/jpeg', 'image/png', 'application/pdf'),
             'digest': ref('digest')}), 2), 'minItems': 1, 'uniqueItems': True},
         'deadline_at': ref('timestamp')}),
    obj({**MESSAGE, 'kind': {'const': 'extract.succeeded'}, 'result': ref('licence')}),
    obj({**MESSAGE, 'kind': {'const': 'extract.failed'}, 'error': ref('error')})]}


def used_defs(schema):
    found = {}
    def visit(node):
        if isinstance(node, dict):
            if '$ref' in node:
                name = node['$ref'].split('/')[-1]
                if name not in found:
                    found[name] = DEFS[name]
                    visit(DEFS[name])
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)
    visit(schema)
    return dict(sorted(found.items()))


def build():
    schemas = {
        'extraction-envelope': (EXTRACTION, 'Transient generic extraction envelope'),
        'do-driver-licence': (LICENCE, 'Transient Dominican Republic driver licence extraction'),
        'reviewed-result': (REVIEWED, 'Confirmed DR driver licence result for persistence'),
        'client-intake': (INTAKE, 'Minimal reviewed identity projection for client intake'),
        'error': (ERROR, 'Structured error without input payloads or exception messages'),
        'worker-contract': (WORKER, 'DR extraction worker request and terminal response messages'),
    }
    DEST.mkdir(parents=True, exist_ok=True)
    for name, (schema, title) in schemas.items():
        document = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
                    '$id': BASE + name + '.schema.json', 'title': title,
                    'description': 'Contract version 1.0.0. See architecture and privacy requirements in the package documentation.',
                    **schema, '$defs': used_defs(schema)}
        (DEST / (name + '.schema.json')).write_text(json.dumps(document, indent=2) + '\n')

if __name__ == '__main__':
    build()
