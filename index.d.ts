export type SchemaName = 'extraction-envelope' | 'do-driver-licence' | 'reviewed-result' |
  'client-intake' | 'error' | 'worker-contract';
export const version: string;
export const schemaNames: readonly SchemaName[];
export function loadSchema(name: SchemaName): Record<string, unknown>;
