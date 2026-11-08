// Adapted from DTU-TEAM-2/smart-cafe-management, 667b580f89d63c7caf176d26869a2b2dbb5e25c8.
import { readFile, readdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const loadRegistry = async () => JSON.parse(await readFile(resolve(root, '.agents/registry.json'), 'utf8'));
export async function routeSkills(domain, registry) {
  registry ??= await loadRegistry();
  const route = registry.routes[domain];
  if (!route) throw new Error(`Unknown domain: ${domain}`);
  return route.map(id => registry.skills.find(skill => skill.id === id));
}
export async function checkRegistry(directory = root) {
  const registry = JSON.parse(await readFile(resolve(directory, '.agents/registry.json'), 'utf8'));
  const ids = new Set(), folders = new Set();
  for (const skill of registry.skills) {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(skill.id) || skill.id.length > 64 || !/^[a-z0-9-]+$/.test(skill.folder)) throw new Error('Invalid skill identifier/folder');
    if (ids.has(skill.id) || folders.has(skill.folder)) throw new Error(`Duplicate skill: ${skill.id}`);
    ids.add(skill.id); folders.add(skill.folder);
    const source = (await readFile(resolve(directory, '.agents/skills', skill.folder, 'SKILL.md'), 'utf8')).replaceAll('\r\n', '\n');
    const frontmatter = source.match(/^---\n([\s\S]*?)\n---/)?.[1];
    if (!frontmatter || !new RegExp(`^name: ${skill.id}$`, 'm').test(frontmatter) || !/^description:\s*\S/m.test(frontmatter)) throw new Error(`Inconsistent frontmatter: ${skill.folder}`);
  }
  for (const entry of await readdir(resolve(directory, '.agents/skills'), {withFileTypes: true})) {
    if (entry.isDirectory() && !folders.has(entry.name)) throw new Error(`Unregistered skill: ${entry.name}`);
  }
  for (const [domain, route] of Object.entries(registry.routes)) {
    if (!route.length || new Set(route).size !== route.length || route.some(id => !ids.has(id))) throw new Error(`Invalid route: ${domain}`);
  }
  return registry;
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const [command = 'list', domain] = process.argv.slice(2);
  try {
    if (command === 'check') {
      const registry = await checkRegistry();
      console.log(`Skill registry OK: ${registry.skills.length} skills, ${Object.keys(registry.routes).length} routes.`);
    } else {
      if (!['list', 'route'].includes(command)) throw new Error('Usage: node scripts/skills.mjs [check|list|route <domain>]');
      for (const skill of command === 'route' ? await routeSkills(domain) : (await loadRegistry()).skills) console.log(`${skill.id} — .agents/skills/${skill.folder}/SKILL.md`);
    }
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
