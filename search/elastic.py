"""Elasticsearch indexing and query helpers for AuctionItem records."""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError
from elasticsearch.exceptions import NotFoundError, TransportError

from analysis.schema import AuctionItem

INDEX_NAME = "auctionote-items"
DEFAULT_ELASTIC_URL = "http://localhost:9200"

logger = logging.getLogger(__name__)

_SETTINGS: dict[str, Any] = {
    "analysis": {
        "analyzer": {
            "auctionote_text": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase"],
            }
        }
    }
}

_MAPPINGS: dict[str, Any] = {
    "dynamic": "strict",
    "properties": {
        "id": {"type": "keyword"},
        "case_no": {"type": "keyword"},
        "item_no": {"type": "integer"},
        "court": {"type": "keyword"},
        "auction_date": {"type": "date"},
        "appraisal_price": {"type": "long"},
        "min_bid_price": {"type": "long"},
        "failed_count": {"type": "integer"},
        "address": {
            "type": "text",
            "analyzer": "auctionote_text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "use_type": {"type": "keyword"},
        "area_m2": {"type": "float"},
        "status": {"type": "keyword"},
        "source_url": {"type": "keyword"},
        "search_text": {"type": "text", "analyzer": "auctionote_text"},
    },
}


def item_id(item: AuctionItem) -> str:
    return f"{item.case_no}:{item.item_no}"


def create_client(url: str = DEFAULT_ELASTIC_URL) -> Elasticsearch:
    return Elasticsearch(url, request_timeout=1.0, retry_on_timeout=False, max_retries=0)


def is_available(client: Elasticsearch) -> bool:
    try:
        return bool(client.ping())
    except (ElasticConnectionError, TransportError):
        return False


def ensure_index(
    client: Elasticsearch, *, index_name: str = INDEX_NAME, recreate: bool = False
) -> None:
    if recreate:
        try:
            client.indices.delete(index=index_name)
        except NotFoundError:
            pass

    if client.indices.exists(index=index_name):
        return

    client.indices.create(
        index=index_name,
        settings=_SETTINGS,
        mappings=_MAPPINGS,
    )


def item_to_document(item: AuctionItem) -> dict[str, Any]:
    return {
        "id": item_id(item),
        "case_no": item.case_no,
        "item_no": item.item_no,
        "court": item.court,
        "auction_date": item.auction_date.isoformat(),
        "appraisal_price": item.appraisal_price,
        "min_bid_price": item.min_bid_price,
        "failed_count": item.failed_count,
        "address": item.address,
        "use_type": item.use_type,
        "area_m2": item.area_m2,
        "status": item.status,
        "source_url": item.source_url,
        "search_text": " ".join(
            [
                item.case_no,
                item.court,
                item.address,
                item.use_type,
                item.status,
            ]
        ),
    }


def document_to_item(document: dict[str, Any]) -> AuctionItem:
    return AuctionItem(
        case_no=document["case_no"],
        item_no=document["item_no"],
        court=document["court"],
        auction_date=date.fromisoformat(document["auction_date"]),
        appraisal_price=document["appraisal_price"],
        min_bid_price=document["min_bid_price"],
        failed_count=document["failed_count"],
        address=document["address"],
        use_type=document["use_type"],
        area_m2=document["area_m2"],
        status=document["status"],
        source_url=document["source_url"],
    )


def index_items(
    client: Elasticsearch,
    items: list[AuctionItem],
    *,
    index_name: str = INDEX_NAME,
    refresh: bool = True,
) -> int:
    if not items:
        return 0

    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": item_id(item),
            "_source": item_to_document(item),
        }
        for item in items
    ]
    ok_count, _ = helpers.bulk(client, actions, refresh=refresh)
    return int(ok_count)


def search_items(
    client: Elasticsearch,
    *,
    query: str | None = None,
    use_types: list[str] | None = None,
    courts: list[str] | None = None,
    min_failed: int | None = None,
    index_name: str = INDEX_NAME,
    size: int = 100,
) -> list[AuctionItem]:
    must: list[dict[str, Any]] = []
    filters: list[dict[str, Any]] = []

    if query and query.strip():
        must.append(
            {
                "multi_match": {
                    "query": query.strip(),
                    "fields": ["search_text^2", "address^3", "case_no", "court"],
                    "operator": "and",
                }
            }
        )
    else:
        must.append({"match_all": {}})

    if use_types:
        filters.append({"terms": {"use_type": use_types}})
    if courts:
        filters.append({"terms": {"court": courts}})
    if min_failed is not None:
        filters.append({"range": {"failed_count": {"gte": min_failed}}})

    response = client.search(
        index=index_name,
        query={"bool": {"must": must, "filter": filters}},
        sort=[
            {"_score": {"order": "desc"}},
            {"auction_date": {"order": "asc"}},
            {"case_no": {"order": "asc"}},
        ],
        size=size,
    )
    return [document_to_item(hit["_source"]) for hit in response["hits"]["hits"]]


def try_search_items(
    client: Elasticsearch,
    *,
    query: str | None = None,
    use_types: list[str] | None = None,
    courts: list[str] | None = None,
    min_failed: int | None = None,
    index_name: str = INDEX_NAME,
    size: int = 100,
) -> list[AuctionItem] | None:
    try:
        if not is_available(client):
            return None
        return search_items(
            client,
            query=query,
            use_types=use_types,
            courts=courts,
            min_failed=min_failed,
            index_name=index_name,
            size=size,
        )
    except (NotFoundError, TransportError, ElasticConnectionError) as exc:
        logger.info("Elasticsearch search unavailable: %s", exc)
        return None
