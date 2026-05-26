import * as esbuild from 'esbuild';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const adminDir = path.resolve(__dirname, '../src/admin');

const DELETE_ONLY = new Set([
  'extend-theme-types.d.ts',
  'vite-env.d.ts',
  'main.tsx',
]);

function walk(dir, acc = []) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) walk(full, acc);
    else if (/\.tsx?$/.test(name)) acc.push(full);
  }
  return acc;
}

function patchImports(code) {
  return code
    .replace(/from 'src\//g, "from '@admin/")
    .replace(/from "src\//g, 'from "@admin/')
    .replace(/import\('src\//g, "import('@admin/");
}

function stripTypeOnlyLines(code) {
  return code
    .replace(/^import type .+;\r?\n/gm, '')
    .replace(/^export type .+;\r?\n/gm, '');
}

function patchConfigGlobal(code) {
  return code.replace(
    /from ['"]\.\.\/package\.json['"]/,
    "from '../../package.json'"
  );
}

const files = walk(adminDir);
let ok = 0;
let fail = 0;
let deletedOnly = 0;

for (const file of files) {
  const base = path.basename(file);
  if (DELETE_ONLY.has(base)) {
    fs.unlinkSync(file);
    deletedOnly += 1;
    continue;
  }

  let content = patchImports(fs.readFileSync(file, 'utf8'));
  content = stripTypeOnlyLines(content);
  const loader = file.endsWith('.tsx') ? 'tsx' : 'ts';
  const outFile = file.replace(/\.tsx$/, '.jsx').replace(/\.ts$/, '.js');

  try {
    const result = await esbuild.transform(content, {
      loader,
      format: 'esm',
      target: 'es2020',
      jsx: 'preserve',
      tsconfigRaw: {
        compilerOptions: {
          jsx: 'preserve',
          verbatimModuleSyntax: false,
        },
      },
    });

    let code = result.code;
    if (base === 'config-global.ts' || outFile.endsWith(`${path.sep}config-global.js`)) {
      code = patchConfigGlobal(code);
    }

    fs.writeFileSync(outFile, code);
    fs.unlinkSync(file);
    ok += 1;
  } catch (err) {
    console.error(`FAIL ${file}:`, err.message);
    fail += 1;
  }
}

const adminAppTsx = path.join(adminDir, 'AdminApp.tsx');
if (fs.existsSync(adminAppTsx)) fs.unlinkSync(adminAppTsx);

const adminAppJsx = path.join(adminDir, 'AdminApp.jsx');
if (!fs.existsSync(adminAppJsx) && !fs.existsSync(adminAppJsx)) {
  // ensure exists: already may be present
}

console.log(
  JSON.stringify({ converted: ok, failed: fail, deletedOnly, adminAppJsx: fs.existsSync(adminAppJsx) })
);
