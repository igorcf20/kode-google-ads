---
name: gestao-google-ads
description: Gestão e análise das contas Google Ads dos nossos clientes (Sintraperi, Kodemi) com o servidor MCP google-ads. Usar em qualquer pedido sobre Google Ads, campanhas, anúncios, palavras-chave, termos de pesquisa, orçamento, CPC, conversões, leads pagas ou relatórios ("como estão as campanhas da Kodemi", "relatório Google Ads da Sintraperi", "palavras-chave negativas", "custo por lead").
---

# Gestão Google Ads

## 1. Identificar o cliente

Cada cliente tem um perfil em `clientes/<cliente>.md` (nesta pasta da skill) com o
ID da conta, o negócio, as páginas de destino e as conversões. **Ler o perfil antes
de qualquer consulta.**

| Cliente | Perfil |
|---|---|
| Sintraperi | `clientes/sintraperi.md` (+ `-catalogo.json`, `-limites.json`) |
| Kodemi | `clientes/kodemi.md` |

- Se o pedido não disser o cliente e houver ambiguidade, perguntar.
- Se o `customer_id` do perfil estiver por preencher, chamar
  `customers_list_accessible_customers` e confirmar com o utilizador qual é a conta
  (depois sugerir atualizar o perfil).
- Nunca misturar dados de clientes diferentes no mesmo relatório, salvo pedido explícito.
- Cliente novo: copiar `clientes/_modelo.md`.

## 2. Ferramentas

### Ler — servidor MCP `google-ads`

- `customers_list_accessible_customers` — contas acessíveis com as credenciais.
- `metadata_get_resource_metadata` (`resource`) — confirmar campos antes de escrever GAQL.
- `search_search` (`customer_id` só dígitos, `query` GAQL).

### Alterar — `scripts/ads-write.sh` (na pasta do plugin `google-ads`)

Aplica um plano JSON (formato no topo de `scripts/ads_write.py`): palavras-chave,
negativas, anúncios RSA, pausar/ativar e orçamentos. Sempre por esta ordem:

1. `ads-write.sh plano.json --limites clientes/<cliente>-limites.json` → a API valida
   (validate_only), nada muda. Corrigir até passar.
2. `... --aplicar` → executa o que os limites deixam aplicar sem aprovação.
3. Se responder **PRECISA DE APROVAÇÃO**: mostrar o plano ao utilizador e, só depois do
   "sim" explícito dele para esse plano, repetir com `--aplicar --aprovado`.

Nunca editar o ficheiro de limites para contornar uma recusa — os limites só mudam a
pedido do utilizador. Cada execução fica em `clientes/alteracoes/<cliente>.jsonl`:
trabalhar a partir do repositório `kode-google-ads` (não da cópia instalada do plugin)
e fazer commit desse registo.

Se as ferramentas de leitura não existirem na sessão: ver o README do repositório
`kode-google-ads` (variáveis de ambiente em falta ou servidor não aprovado).
Não inventar números.

## 3. Ciclo de gestão (autonomia)

O utilizador quer que eu proponha **e** resolva. Em cada sessão de gestão:

1. **Ler**: desempenho (30 dias vs. anteriores), termos de pesquisa, palavras-chave,
   anúncios, parcela de impressões, conversões.
2. **Ligar ao negócio**: comparar com `clientes/<cliente>-catalogo.json` (serviços,
   páginas, sinais/sintomas que as pessoas pesquisam, fotos). Cada serviço deve ter o seu
   grupo de anúncios, palavras-chave próprias e anúncios que apontam para a sua página.
   Se o site mudou, regenerar o catálogo:
   `node scripts/catalogo-do-site.mjs <repo-do-site> clientes/<cliente>-catalogo.json <dominio>`.
3. **Decidir** por impacto: cortar desperdício (negativas, pausar palavras-chave sem
   conversões com custo relevante), cobrir serviços sem anúncios, melhorar anúncios
   com CTR baixo.
4. **Aplicar** o que está em `aplicar_sem_aprovacao`; agrupar o resto num plano e pedir
   aprovação numa só mensagem.
5. **Relatar**: o que mudou, porquê, e o que medir na próxima sessão.

Fotos: as imagens do catálogo (caminhos no repositório do site) servem para recursos de
imagem; o envio de imagens ainda não está na ferramenta — propor e indicar quais.

## 4. Regras

1. Alterações só pela `ads-write.sh`, dentro dos limites do cliente. Nunca dizer que
   algo foi alterado sem a resposta **APLICADO** da ferramenta.
2. Dinheiro: `*_micros` ÷ 1 000 000, na moeda da conta (`customer.currency_code`).
3. Indicar sempre o período. Por omissão últimos 30 dias
   (`segments.date DURING LAST_30_DAYS`) e comparar com o período anterior quando se
   fala de subidas/quedas.
4. Parcelas de impressões vêm em decimal (0.35 = 35%) ou como texto `"< 0.10"`.
5. Quedas de conversões/leads ou perda de parcela de impressões → seguir a skill
   `google-ads-api-account-diagnostics`.
6. Antes de concluir "não há leads", ver as ações de conversão (`conversion_action`):
   origem, estado e se são primárias.
7. Responder em português de Portugal, com tabelas curtas e as recomendações no fim.

## 5. GAQL úteis

```sql
-- Desempenho por campanha
SELECT campaign.id, campaign.name, campaign.status, campaign_budget.amount_micros,
       metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.ctr,
       metrics.conversions, metrics.cost_per_conversion
FROM campaign
WHERE segments.date DURING LAST_30_DAYS AND campaign.status != 'REMOVED'
ORDER BY metrics.cost_micros DESC

-- Termos de pesquisa com custo e sem conversões (candidatos a negativas)
SELECT search_term_view.search_term, campaign.name, ad_group.name,
       metrics.cost_micros, metrics.clicks, metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_30_DAYS AND metrics.conversions = 0 AND metrics.cost_micros > 0
ORDER BY metrics.cost_micros DESC
LIMIT 50

-- URLs finais dos anúncios (comparar com as páginas do perfil)
SELECT ad_group_ad.ad.final_urls, ad_group_ad.status, campaign.name, ad_group.name
FROM ad_group_ad
WHERE ad_group_ad.status != 'REMOVED'

-- Ações de conversão
SELECT conversion_action.name, conversion_action.type, conversion_action.status,
       conversion_action.primary_for_goal, conversion_action.origin
FROM conversion_action
```
