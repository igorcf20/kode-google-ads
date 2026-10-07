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
| Sintraperi | `clientes/sintraperi.md` |
| Kodemi | `clientes/kodemi.md` |

- Se o pedido não disser o cliente e houver ambiguidade, perguntar.
- Se o `customer_id` do perfil estiver por preencher, chamar
  `customers_list_accessible_customers` e confirmar com o utilizador qual é a conta
  (depois sugerir atualizar o perfil).
- Nunca misturar dados de clientes diferentes no mesmo relatório, salvo pedido explícito.
- Cliente novo: copiar `clientes/_modelo.md`.

## 2. Ferramentas (servidor MCP `google-ads`)

- `customers_list_accessible_customers` — contas acessíveis com as credenciais.
- `metadata_get_resource_metadata` (`resource`) — confirmar campos antes de escrever GAQL.
- `search_search` (`customer_id` só dígitos, `query` GAQL).

Se as ferramentas não existirem na sessão: ver o README do repositório
`google-ads-toolkit` (variáveis de ambiente em falta ou servidor não aprovado).
Não inventar números.

## 3. Regras

1. **Só leitura.** O MCP não altera contas. Entregar recomendações concretas
   (o quê, onde, porquê, impacto esperado) para aplicar na interface do Google Ads.
   Nunca dizer que algo foi alterado.
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

## 4. GAQL úteis

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
