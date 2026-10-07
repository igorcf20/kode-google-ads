# google-ads-toolkit

Plugin do Claude Code para gerir e analisar as contas Google Ads dos nossos clientes
(**Sintraperi** e **Kodemi**). Usa o
[servidor MCP oficial do Google Ads](https://github.com/googleads/google-ads-mcp)
e as skills de Google Ads de [google/skills](https://github.com/google/skills).

## Conteúdo

| Caminho | O quê |
|---|---|
| `skills/gestao-google-ads/` | Skill principal: regras de análise, GAQL úteis e um perfil por cliente em `clientes/`. |
| `skills/google-ads-api-quickstart/` | (Google) Obter developer token, OAuth e refresh token. |
| `skills/google-ads-api-mcp-setup/` | (Google) Instalar/configurar o servidor MCP. |
| `skills/google-ads-api-account-diagnostics/` | (Google) Diagnosticar quedas de conversões/leads e parcela de impressões. |
| `.mcp.json` + `scripts/google-ads-mcp.sh` | Servidor MCP `google-ads` (versão fixada, via `uvx` ou `pipx`). |
| `.claude-plugin/` | Manifestos do plugin e do marketplace. |

As skills da Google são cópias de `google/skills@8a1ac05` (Apache-2.0,
`skills/LICENSE-google-skills`).

> O servidor MCP é **só de leitura** (`customers_list_accessible_customers`,
> `metadata_get_resource_metadata`, `search_search`). O Claude analisa e recomenda; as
> alterações fazem-se na interface do Google Ads.

## Instalação

### Opção A — abrir este repositório no Claude Code (inclui claude.ai/code)

O `.claude/settings.json` regista o marketplace e ativa o plugin: ao abrir uma sessão
neste repositório, o Claude Code propõe instalá-lo. Aceitar e aprovar o servidor
`google-ads`.

### Opção B — disponível em qualquer projeto (Claude Code local)

```
/plugin marketplace add igorcf20/google-ads-toolkit
/plugin install google-ads@google-ads-toolkit
```

ou no terminal:

```bash
claude plugin marketplace add igorcf20/google-ads-toolkit
claude plugin install google-ads@google-ads-toolkit
```

Como o repositório é privado, o `git` local tem de ter acesso a ele (ex.: `gh auth login`).
Atualizar: `claude plugin marketplace update google-ads-toolkit`.

Requisitos: Python 3.12+ e [`uv`](https://docs.astral.sh/uv/) (ou `pipx`).

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

Copiar os IDs para `skills/gestao-google-ads/clientes/sintraperi.md` e `kodemi.md`.

## Exemplos

- "Resumo dos últimos 30 dias da Sintraperi por campanha: custo, cliques, CTR, conversões, custo por conversão."
- "Termos de pesquisa da Kodemi que gastaram sem converter — sugere negativas."
- "As leads da Sintraperi caíram esta semana, diagnostica."
- "Compara Sintraperi e Kodemi: custo por lead no último mês."

## Novo cliente

Copiar `skills/gestao-google-ads/clientes/_modelo.md`, preencher e acrescentar à tabela
em `skills/gestao-google-ads/SKILL.md`.
