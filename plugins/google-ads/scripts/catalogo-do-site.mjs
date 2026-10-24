#!/usr/bin/env node
// Gera o catálogo de serviços de um cliente a partir do repositório do site.
// Uso: node catalogo-do-site.mjs <repo-do-site> <saida.json> <dominio>
// Hoje suporta o formato da Sintraperi (src/pages/services/serviceLandings.ts).
import { createRequire } from "node:module";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const [siteArg, out, domain = "https://sintraperi.pt"] = process.argv.slice(2);
const site = siteArg && path.resolve(siteArg);
if (!siteArg || !out) {
  console.error("uso: catalogo-do-site.mjs <repo-do-site> <saida.json> [dominio]");
  process.exit(1);
}
// esbuild vem das dependências do próprio site.
const { build } = createRequire(path.resolve(site, "package.json"))("esbuild");
const entry = path.join(site, "src/pages/services/serviceLandings.ts");
const tmp = path.join(mkdtempSync(path.join(tmpdir(), "catalogo-")), "landings.cjs");

// Imagens: em vez do ficheiro, devolve o caminho no repositório do site.
const images = {
  name: "images",
  setup(b) {
    b.onResolve({ filter: /^@\// }, (a) => ({ path: path.join(site, "src", a.path.slice(2)) }));
    b.onLoad({ filter: /\.(webp|jpe?g|png|svg)$/ }, (a) => ({
      contents: `module.exports = ${JSON.stringify(path.relative(site, a.path))};`,
      loader: "js",
    }));
  },
};
await build({ entryPoints: [entry], bundle: true, platform: "node", format: "cjs", outfile: tmp, plugins: [images], logLevel: "error" });
const { serviceLandings } = createRequire(import.meta.url)(tmp);

const servicos = Object.values(serviceLandings).map((s) => ({
  slug: s.slug,
  servico: s.title,
  url: `${domain}/${s.slug}`,
  meta_title: s.metaTitle,
  meta_description: s.metaDescription,
  subtitulo: s.hero?.subtitle,
  sinais: s.signs ?? [],
  beneficios: (s.benefits ?? []).map((b) => b.title),
  equipamento: (s.equipment ?? []).map((e) => e.title),
  faq: (s.faq ?? []).map((f) => f.q),
  imagens: [...new Set([s.image, ...(s.media ?? []).map((m) => m.src)].filter(Boolean))],
}));
writeFileSync(out, JSON.stringify({ gerado_de: path.basename(site), dominio: domain, servicos }, null, 2) + "\n");
console.log(`${servicos.length} serviços -> ${out}`);
