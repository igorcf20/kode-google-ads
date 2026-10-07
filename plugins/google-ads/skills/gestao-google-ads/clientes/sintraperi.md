# Sintraperi

- **customer_id:** _por preencher_ (10 dígitos, sem hífens)
- **Site:** https://sintraperi.pt
- **Repositório do site:** `igorcf20/sintrapeript`
- **Moeda / zona:** EUR / Portugal

## Negócio
Deteção de fugas, infiltrações e humidades, peritagem para seguradoras, inspeção de
tubagens, termografia e inspeção com drone.

## Objetivos
Leads: telefone, WhatsApp, formulário de contacto e pedido de orçamento (`/orcamento`).

## Páginas de destino
Landing pages de serviço (criadas para sitelinks):
- `/detecao-de-fugas`
- `/infiltracoes-e-humidades`
- `/peritagem-para-seguradoras`
- `/inspecao-de-tubagens`
- `/inspecao-com-drone`
- `/inspecao-termografica-com-drone`
- `/detecao-de-fugas-com-gas-tracador`

Outras: `/servicos`, `/contactos`, `/orcamento`.

## Conversões
- O site carrega a etiqueta Google Ads (`AW-...`) configurada em *Admin → Configurações
  → Rastreamento*, só com consentimento de marketing.
- Eventos enviados pelo site (`src/lib/tracking.ts`): `click_whatsapp`, `click_phone`,
  `click_email`, `submit_contact_form`, `click_request_assessment`, `click_quote`,
  `click_contact_technician`.
- `trackAdsConversion` existe no código mas não é chamado: as conversões no Google Ads
  dependem de importação do GA4 (eventos-chave). Confirmar em `conversion_action`.

## Notas
_por preencher_
