#!/usr/bin/env python3
"""Aplica um plano de alterações a uma conta Google Ads, com limites de segurança.

Uso:
  ads_write.py <plano.json> --limites <cliente-limites.json> [--aplicar] [--aprovado]

Sem --aplicar, o plano é só validado pela API (validate_only) — nada muda.
Com --aplicar, operações fora de "aplicar_sem_aprovacao" exigem --aprovado
(o utilizador disse "sim" a este plano). Cada execução é registada em
alteracoes/<cliente>.jsonl, ao lado do ficheiro de limites.

Formato do plano:
{
  "customer_id": "1234567890",
  "motivo": "porquê destas alterações",
  "operacoes": [
    {"tipo": "add_negative_keywords", "campaign_id": "1", "keywords": [{"texto": "gratis", "match": "PHRASE"}]},
    {"tipo": "add_keywords", "ad_group_id": "2", "keywords": [{"texto": "detecao de fugas sintra", "match": "PHRASE"}], "cpc_eur": 1.5},
    {"tipo": "create_rsa", "ad_group_id": "2", "final_url": "https://sintraperi.pt/detecao-de-fugas",
     "headlines": ["..."], "descriptions": ["..."], "path1": "fugas", "path2": "sintra"},
    {"tipo": "set_status", "recurso": "campaign|ad_group|ad_group_criterion|ad_group_ad", "id": "123 ou 2~456", "status": "PAUSED|ENABLED"},
    {"tipo": "set_budget", "campaign_budget_id": "9", "diario_eur": 20}
  ]
}

Credenciais: GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET,
GOOGLE_ADS_REFRESH_TOKEN e (com MCC) GOOGLE_ADS_LOGIN_CUSTOMER_ID.
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

MATCH = {"EXACT", "PHRASE", "BROAD"}
STATUS = {"ENABLED", "PAUSED"}
RECURSOS = {"campaign", "ad_group", "ad_group_criterion", "ad_group_ad"}


class Recusado(Exception):
    pass


def digitos(valor):
    return re.sub(r"\D", "", str(valor))


def chave_aprovacao(op):
    return f"set_status:{op['recurso']}" if op["tipo"] == "set_status" else op["tipo"]


def verificar(plano, limites):
    """Regras locais, antes de qualquer chamada à API. Devolve a lista de problemas."""
    erros = []
    if limites.get("customer_id") and digitos(plano.get("customer_id")) != digitos(limites["customer_id"]):
        erros.append("customer_id do plano não é o do cliente destes limites")
    if not plano.get("motivo"):
        erros.append("plano sem 'motivo'")
    dominios = set(limites.get("dominios_permitidos", []))
    for i, op in enumerate(plano.get("operacoes", [])):
        onde = f"operação {i} ({op.get('tipo')})"
        t = op.get("tipo")
        if t in ("add_negative_keywords", "add_keywords"):
            for k in op.get("keywords", []):
                if k.get("match") not in MATCH:
                    erros.append(f"{onde}: match inválido em {k}")
                if not k.get("texto") or len(k["texto"]) > 80:
                    erros.append(f"{onde}: palavra-chave vazia ou > 80 caracteres")
            if t == "add_keywords" and op.get("cpc_eur") is not None and op["cpc_eur"] > limites.get("cpc_max_eur", 0):
                erros.append(f"{onde}: CPC {op['cpc_eur']} € acima do limite {limites.get('cpc_max_eur')} €")
        elif t == "create_rsa":
            h, d = op.get("headlines", []), op.get("descriptions", [])
            if not 3 <= len(h) <= 15:
                erros.append(f"{onde}: precisa de 3 a 15 títulos")
            if not 2 <= len(d) <= 4:
                erros.append(f"{onde}: precisa de 2 a 4 descrições")
            erros += [f"{onde}: título > 30 caracteres: {x!r}" for x in h if len(x) > 30]
            erros += [f"{onde}: descrição > 90 caracteres: {x!r}" for x in d if len(x) > 90]
            erros += [f"{onde}: {p} > 15 caracteres" for p in ("path1", "path2") if len(op.get(p) or "") > 15]
            host = urlparse(op.get("final_url", "")).hostname or ""
            if not any(host == dom or host.endswith("." + dom) for dom in dominios):
                erros.append(f"{onde}: final_url fora dos domínios do cliente ({host or 'vazio'})")
        elif t == "set_status":
            if op.get("recurso") not in RECURSOS or op.get("status") not in STATUS:
                erros.append(f"{onde}: recurso/status inválido")
        elif t == "set_budget":
            teto = limites.get("orcamento_diario_max_eur_por_campanha")
            if teto is None:
                erros.append(f"{onde}: orçamentos bloqueados — defina orcamento_diario_max_eur_por_campanha nos limites")
            elif not 0 < op.get("diario_eur", 0) <= teto:
                erros.append(f"{onde}: orçamento diário {op.get('diario_eur')} € fora de ]0, {teto}] €")
        else:
            erros.append(f"{onde}: tipo desconhecido")
    return erros


def precisa_aprovacao(plano, limites):
    livres = set(limites.get("aplicar_sem_aprovacao", []))
    return sorted({chave_aprovacao(op) for op in plano["operacoes"]} - livres)


def cliente_api():
    from google.ads.googleads.client import GoogleAdsClient

    cfg = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    if os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
        cfg["login_customer_id"] = digitos(os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"])
    return GoogleAdsClient.load_from_dict(cfg)


def construir(client, cid, plano):
    """Traduz o plano em MutateOperations da GoogleAdsService."""
    from google.api_core import protobuf_helpers

    ga = client.get_service("GoogleAdsService")
    enums = client.enums
    ops = []

    def nova():
        return client.get_type("MutateOperation")

    for op in plano["operacoes"]:
        t = op["tipo"]
        if t == "add_negative_keywords":
            for k in op["keywords"]:
                m = nova()
                c = m.campaign_criterion_operation.create
                c.campaign = ga.campaign_path(cid, digitos(op["campaign_id"]))
                c.negative = True
                c.keyword.text = k["texto"]
                c.keyword.match_type = enums.KeywordMatchTypeEnum[k["match"]]
                ops.append(m)
        elif t == "add_keywords":
            for k in op["keywords"]:
                m = nova()
                c = m.ad_group_criterion_operation.create
                c.ad_group = ga.ad_group_path(cid, digitos(op["ad_group_id"]))
                c.status = enums.AdGroupCriterionStatusEnum.ENABLED
                c.keyword.text = k["texto"]
                c.keyword.match_type = enums.KeywordMatchTypeEnum[k["match"]]
                if op.get("cpc_eur") is not None:
                    c.cpc_bid_micros = int(round(op["cpc_eur"] * 1_000_000))
                ops.append(m)
        elif t == "create_rsa":
            m = nova()
            a = m.ad_group_ad_operation.create
            a.ad_group = ga.ad_group_path(cid, digitos(op["ad_group_id"]))
            a.status = enums.AdGroupAdStatusEnum.ENABLED
            a.ad.final_urls.append(op["final_url"])
            for texto in op["headlines"]:
                asset = client.get_type("AdTextAsset")
                asset.text = texto
                a.ad.responsive_search_ad.headlines.append(asset)
            for texto in op["descriptions"]:
                asset = client.get_type("AdTextAsset")
                asset.text = texto
                a.ad.responsive_search_ad.descriptions.append(asset)
            if op.get("path1"):
                a.ad.responsive_search_ad.path1 = op["path1"]
            if op.get("path2"):
                a.ad.responsive_search_ad.path2 = op["path2"]
            ops.append(m)
        elif t == "set_status":
            m = nova()
            rec, ident = op["recurso"], str(op["id"])
            if rec == "campaign":
                obj = m.campaign_operation.update
                obj.resource_name = ga.campaign_path(cid, digitos(ident))
                obj.status = enums.CampaignStatusEnum[op["status"]]
                alvo = m.campaign_operation
            elif rec == "ad_group":
                obj = m.ad_group_operation.update
                obj.resource_name = ga.ad_group_path(cid, digitos(ident))
                obj.status = enums.AdGroupStatusEnum[op["status"]]
                alvo = m.ad_group_operation
            elif rec == "ad_group_criterion":
                ag, crit = ident.split("~")
                obj = m.ad_group_criterion_operation.update
                obj.resource_name = ga.ad_group_criterion_path(cid, digitos(ag), digitos(crit))
                obj.status = enums.AdGroupCriterionStatusEnum[op["status"]]
                alvo = m.ad_group_criterion_operation
            else:
                ag, ad = ident.split("~")
                obj = m.ad_group_ad_operation.update
                obj.resource_name = ga.ad_group_ad_path(cid, digitos(ag), digitos(ad))
                obj.status = enums.AdGroupAdStatusEnum[op["status"]]
                alvo = m.ad_group_ad_operation
            client.copy_from(alvo.update_mask, protobuf_helpers.field_mask(None, obj._pb))
            ops.append(m)
        elif t == "set_budget":
            m = nova()
            b = m.campaign_budget_operation.update
            b.resource_name = ga.campaign_budget_path(cid, digitos(op["campaign_budget_id"]))
            b.amount_micros = int(round(op["diario_eur"] * 1_000_000))
            client.copy_from(m.campaign_budget_operation.update_mask, protobuf_helpers.field_mask(None, b._pb))
            ops.append(m)
    return ops


def registar(limites_path, cliente, entrada):
    pasta = Path(limites_path).parent / "alteracoes"
    pasta.mkdir(exist_ok=True)
    with open(pasta / f"{cliente}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plano")
    ap.add_argument("--limites", required=True)
    ap.add_argument("--aplicar", action="store_true", help="executa de verdade (sem isto: só valida)")
    ap.add_argument("--aprovado", action="store_true", help="o utilizador aprovou este plano")
    ap.add_argument("--so-local", action="store_true", help="só as regras locais, sem chamar a API")
    a = ap.parse_args()

    plano = json.load(open(a.plano, encoding="utf-8"))
    limites = json.load(open(a.limites, encoding="utf-8"))
    erros = verificar(plano, limites)
    if erros:
        print("RECUSADO pelas regras locais:\n- " + "\n- ".join(erros))
        return 2
    pendentes = precisa_aprovacao(plano, limites)
    if a.so_local:
        print("OK nas regras locais." + (f" Precisa de aprovação: {', '.join(pendentes)}" if pendentes else ""))
        return 0
    if a.aplicar and pendentes and not a.aprovado:
        print(f"PRECISA DE APROVAÇÃO para: {', '.join(pendentes)}. Mostre o plano ao utilizador e repita com --aprovado.")
        return 3

    from google.ads.googleads.errors import GoogleAdsException

    client = cliente_api()
    cid = digitos(plano["customer_id"])
    ops = construir(client, cid, plano)
    ga = client.get_service("GoogleAdsService")
    entrada = {
        "quando": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "customer_id": cid,
        "motivo": plano["motivo"],
        "aplicado": a.aplicar,
        "aprovado": a.aprovado,
        "operacoes": plano["operacoes"],
    }
    try:
        resp = ga.mutate(customer_id=cid, mutate_operations=ops, validate_only=not a.aplicar)
    except GoogleAdsException as ex:
        problemas = [e.message for e in ex.failure.errors]
        print("ERRO da API Google Ads:\n- " + "\n- ".join(problemas))
        if a.aplicar:
            registar(a.limites, limites.get("cliente", "cliente"), {**entrada, "erro": problemas})
        return 1
    if not a.aplicar:
        print(f"VALIDADO pela API ({len(ops)} operações). Nada foi alterado; use --aplicar para executar.")
        return 0
    criados = [str(r) for r in resp.mutate_operation_responses]
    registar(a.limites, limites.get("cliente", "cliente"), {**entrada, "resultado": criados})
    print(f"APLICADO: {len(ops)} operações.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
