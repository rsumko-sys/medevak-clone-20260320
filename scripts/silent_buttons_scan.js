const fs = require('fs');
const path = require('path');
const root = '/Users/admin/Desktop/MEDEVAK_clone/frontend/src';
const exts = new Set(['.tsx', '.jsx']);
const files = [];

function walk(dir) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p);
    else if (exts.has(path.extname(ent.name))) files.push(p);
  }
}

walk(root);
const out = [];

for (const f of files) {
  const txt = fs.readFileSync(f, 'utf8');
  let i = 0;
  while (true) {
    const s = txt.indexOf('<button', i);
    if (s < 0) break;
    let j = s;
    while (j < txt.length && txt[j] !== '>') j++;
    const tag = txt.slice(s, Math.min(j + 1, txt.length));
    const hasOnClick = /\bonClick\s*=/.test(tag);
    const isSubmit = /\btype\s*=\s*['\"]submit['\"]/.test(tag);
    if (!hasOnClick && !isSubmit) {
      const line = txt.slice(0, s).split('\n').length;
      out.push({
        file: f.replace('/Users/admin/Desktop/MEDEVAK_clone/', ''),
        line,
        tag: tag.replace(/\s+/g, ' ').slice(0, 180),
      });
    }
    i = j + 1;
  }
}

console.log(`silent_buttons=${out.length}`);
out.slice(0, 200).forEach((x) => console.log(`${x.file}:${x.line} ${x.tag}`));
