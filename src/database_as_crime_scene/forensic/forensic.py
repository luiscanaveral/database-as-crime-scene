from dataclasses import dataclass

import pandas as pd
from sqlalchemy import text

from ..common.logger import log
from ..db.connection import get_engine
from .query_builder import QueryBuilder

q = QueryBuilder()


@dataclass
class Forensic:
    conn_string: str

    def init(self):
        pass

    def _get_indexes_metadata(self, as_dataframe=False):
        query = q.get_index_data_query()
        with get_engine().connect() as conn:
            indexes = conn.execute(text(query)).fetchall()
            if as_dataframe:
                return pd.DataFrame(indexes)
            return indexes

    def _get_selectivity(self, as_dataframe=False):
        query = q.get_selectivity_query()
        with get_engine().connect() as conn:
            indexes = conn.execute(text(query)).fetchall()
            if as_dataframe:
                return pd.DataFrame(indexes)
            return indexes

    def check_indexes(self):
        df = self._get_indexes_metadata(True)

        def _get_classification(row):
            idx_scan = row["idx_scan"]
            pct_vs_total = (
                float(row["pct_vs_total"]) if row["pct_vs_total"] is not None else 0
            )
            is_pk = bool(row["is_pk"]) if "is_pk" in row else False
            is_unique = bool(row["is_unique"]) if "is_unique" in row else False
            return self.classify(idx_scan, pct_vs_total, is_pk, is_unique)

        classifications = df.apply(_get_classification, axis=1)
        df["status"] = classifications.apply(lambda x: x[0])
        # df['color'] = classifications.apply(lambda x: x[1])

        def _get_score(row):
            idx_scan = row["idx_scan"]
            pct_vs_heap = (
                float(row["pct_vs_heap"]) if row["pct_vs_heap"] is not None else 0
            )
            pct_vs_total = (
                float(row["pct_vs_total"]) if row["pct_vs_total"] is not None else 0
            )
            is_pk = bool(row["is_pk"]) if "is_pk" in row else False
            is_unique = bool(row["is_unique"]) if "is_unique" in row else False
            return self.compute_score(
                pct_vs_heap, pct_vs_total, idx_scan, is_pk, is_unique
            )

        df["score"] = df.apply(_get_score, axis=1)

        df["index_size"] = df["index_size"].apply(self.format_size)
        if "heap_size" in df:
            df["heap_size"] = df["heap_size"].apply(self.format_size)
        if "total_size" in df:
            df["total_size"] = df["total_size"].apply(self.format_size)

        df_sorted = df.sort_values(by="status")

        df_selectivity = self._get_selectivity(True)
        df_merged = pd.merge(
            df_sorted, df_selectivity, on=["table_name", "index_name"], how="left"
        )

        log(df_merged, log_type="table")

        return df_merged

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def compute_score(self, pct_vs_heap, pct_vs_total, idx_scan, is_pk, is_unique):
        if is_pk:
            return 100  # always safe

        score = 0

        # unique index bonus (0-20)
        if is_unique:
            score += 20

        # size penalty based on pct_vs_total (0–30)
        score += max(0, 30 - pct_vs_total * 0.5)

        # activity bonus (0–50)
        if idx_scan > 1000:
            score += 50
        elif idx_scan > 100:
            score += 30
        elif idx_scan > 0:
            score += 10
        else:
            # penalize heavily unused indexes relative to the heap size
            score -= 20 + pct_vs_heap * 0.5

        return round(max(0, min(100, score)), 1)

    def classify(self, idx_scan, pct_vs_total, is_pk, is_unique):
        if is_pk:
            return "PK", "blue"

        if is_unique:
            return "UNIQUE", "cyan"

        if idx_scan == 0 and pct_vs_total > 20:
            return "CRITICAL", "red"

        if idx_scan < 50 and pct_vs_total > 10:
            return "SUSPICIOUS", "yellow"

        return "HEALTHY", "green"

    def format_size(self, bytes_val):
        return f"{bytes_val / 1024 / 1024:.2f} MB"
