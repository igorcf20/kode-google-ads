# kode-google-ads

Plugins do Claude Code para gerir e analisar as contas Google Ads dos nossos clientes
(**Sintraperi** e **Kodemi**). Usa o
[servidor MCP oficial do Google Ads](https://github.com/googleads/google-ads-mcp)
e as skills de Google Ads de [google/skills](https://github.com/google/skills).

## Plugins

O repositório é um marketplace do Claude Code com 7 plugins. As skills oficiais da
Google (todas as de [google/skills](https://github.com/google/skills)) estão
divididas por área, para se ativar só o que for preciso.

| Plugin | Skills | Custo fixo por sessão* | Conteúdo |
|---|---|---|---|
| `google-ads` | 4 | ~0,8k tokens | Gestão das contas (skill `gestao-google-ads` + perfis em `clientes/`), skills Google Ads API e servidor MCP `google-ads`. |
| `google-ads-dev` | 11 | ~1,7k | Google Mobile Ads SDK, IMA SDK/DAI, Data Manager API (públicos e conversões offline). |
| `google-analytics` | 2 | ~0,4k | APIs Admin e Data do GA4. |
| `google-cloud-essencial` | 13 | ~2,4k | Projeto e credenciais (onboarding, auth, `gcloud`, IAM: erros e gestão de acessos), revisão de segurança, custos, BigQuery (exportações GA4/Google Ads, previsões), Gemini, Cloud Run, Firebase, Cloud Storage. |
| `google-cloud` ⏸ | 118 | ~22k | Restantes skills Google Cloud: GKE, AlloyDB/Cloud SQL/Spanner/Bigtable, Logging/Monitoring, Agent Platform, Genkit, SecOps, Filestore, Airflow, arquitetura. **Desativado.** |
| `google-developers` | 2 | ~0,4k | Encontrar skills Google; consultar documentação oficial. |
| `google-identity` | 1 | ~0,2k | DPoP. |

\* Descrições das skills carregadas em todas as sessões com o plugin ativo; o conteúdo
completo de cada skill só é lido quando é usada.

⏸ `google-cloud` está desativado por ser pesado e pouco relevante para a nossa
atividade. Para o usar: `/plugin` → ativar, ou `true` em `.claude/settings.json`. A
lista das skills essenciais está em `CLOUD_ESSENCIAL` no `scripts/sync-google-skills.sh`
(mover uma skill = editar a lista e correr o script).

Estrutura: `plugins/<plugin>/skills/<skill>/SKILL.md`. As skills da Google são cópias
de `google/skills` no commit em `GOOGLE_SKILLS_COMMIT` (Apache-2.0,
`plugins/*/skills/LICENSE-google-skills`).

> O servidor MCP do Google Ads é **só de leitura** (`customers_list_accessible_customers`,
> `metadata_get_resource_metadata`, `search_search`). O Claude analisa e recomenda; as
> alterações fazem-se na interface do Google Ads.

## Atualizar as skills da Google

```bash
scripts/sync-google-skills.sh        # último main de google/skills
git add -A && git commit -m "chore: sync google/skills"
```

As skills da Google são substituídas pelas versões novas; `gestao-google-ads` e os
perfis de clientes não são tocados. Skills novas entram no plugin da sua área (Ads de
gestão de contas `google-ads-api-*` → `google-ads`; restantes de Ads → `google-ads-dev`).

## Instalação

### Opção A — abrir este repositório no Claude Code (inclui claude.ai/code)

O `.claude/settings.json` regista o marketplace e ativa os plugins (exceto `google-cloud`): ao abrir uma
sessão neste repositório, o Claude Code propõe instalá-los. Aceitar e aprovar o
servidor `google-ads`.

### Opção B — disponível em qualquer projeto (Claude Code local)

```
/plugin marketplace add igorcf20/kode-google-ads
/plugin install google-ads@kode-google-ads
/plugin install google-analytics@kode-google-ads
/plugin install google-ads-dev@kode-google-ads
/plugin install google-cloud-essencial@kode-google-ads
/plugin install google-developers@kode-google-ads
/plugin install google-identity@kode-google-ads
```

Como o repositório é privado, o `git` local tem de ter acesso a ele (ex.: `gh auth login`).
Atualizar: `claude plugin marketplace update kode-google-ads`.

Requisitos do servidor MCP: Python 3.12+ e [`uv`](https://docs.astral.sh/uv/) (ou `pipx`).

## Credenciais

Uma única configuração serve os dois clientes. Recomendado: criar uma **conta de
gestor (MCC)** gratuita e ligar-lhe as contas da Sintraperi e da Kodemi; assim um
developer token e um refresh token dão acesso a ambas. (Sem MCC também funciona se o
utilizador Google das credenciais tiver acesso direto às duas contas.)

1. **Developer token** — no MCC: Ferramentas → Centro de API. O nível *Test* só serve
   contas de teste; para contas reais pedir **Explorer** ou **Basic access**.
2. **OAuth Client ID/Secret** — Google Cloud Console → ativar *Google Ads API* →
   Credenciais → ID de cliente OAuth do tipo *Aplicação para computador*.
3. **Refresh token** — gerado uma vez com o scope `https://www.googleapis.com/auth/adwords`
   (ex.: `generate_user_credentials.py` da biblioteca `google-ads-python`).
   A skill `google-ads-api-quickstart` guia estes passos: pedir ao Claude
   "ajuda-me a obter as credenciais do Google Ads".

Variáveis de ambiente:

| Variável | Obrigatória | Nota |
|---|---|---|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | sim | |
| `GOOGLE_ADS_CLIENT_ID` | sim* | `....apps.googleusercontent.com` |
| `GOOGLE_ADS_CLIENT_SECRET` | sim* | |
| `GOOGLE_ADS_REFRESH_TOKEN` | sim* | |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | com MCC | ID do MCC; hífens removidos automaticamente |
| `GOOGLE_ADS_MCP_VERSION` | não | por omissão `0.0.4` |

\* O `google-ads-mcp` autentica por *Application Default Credentials*; o script converte
estas três variáveis num ficheiro ADC (`~/.config/google-ads-mcp/adc.json`, permissões
600). Alternativa: `gcloud auth application-default login --scopes=https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform`
e definir só o developer token.

Onde definir:
- **claude.ai/code**: definições do ambiente → *Environment variables*; a política de
  rede tem de permitir `googleads.googleapis.com`, `oauth2.googleapis.com` e `pypi.org`.
- **Local**: `~/.bashrc` / `~/.zshrc`.

**Nunca** fazer commit de credenciais neste repositório.

## Verificar

`/mcp` deve mostrar `google-ads` ligado. Depois:

> "Lista as contas Google Ads a que tenho acesso."

Copiar os IDs para `plugins/google-ads/skills/gestao-google-ads/clientes/sintraperi.md` e `kodemi.md`.

## Exemplos

- "Resumo dos últimos 30 dias da Sintraperi por campanha: custo, cliques, CTR, conversões, custo por conversão."
- "Termos de pesquisa da Kodemi que gastaram sem converter — sugere negativas."
- "As leads da Sintraperi caíram esta semana, diagnostica."
- "Compara Sintraperi e Kodemi: custo por lead no último mês."

## Novo cliente

Copiar `plugins/google-ads/skills/gestao-google-ads/clientes/_modelo.md`, preencher e
acrescentar à tabela em `plugins/google-ads/skills/gestao-google-ads/SKILL.md`.
