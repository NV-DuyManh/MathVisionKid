import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export function validateStudentApiBundle(bundle, expectedBase) {
  const bases = [...bundle.matchAll(/https?:\/\/[a-zA-Z0-9.-]+(?::\d+)?\/api\/v1\b/g)].map(match => match[0]);
  if (!bases.includes(expectedBase) || bases.some(base => base !== expectedBase))
    throw new Error('Student export has a missing or stale service address. Clear the export cache and rebuild before publishing.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const [directory, expectedBase] = process.argv.slice(2);
  if (!directory || !expectedBase) throw new Error('Usage: check_student_export.mjs <export-directory> <expected-public-api-base>');
  const chunks = join(directory, '_expo/static/js/web');
  const bundle = readdirSync(chunks).filter(name => name.endsWith('.js')).map(name => readFileSync(join(chunks, name), 'utf8')).join('\n');
  validateStudentApiBundle(bundle, expectedBase);
  console.log('Student export service address verified.');
}
