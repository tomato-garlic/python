# -*- coding: utf-8 -*-
"""
data_recorder.py
================
データ記録・閾値算出モジュール

試行ごとのデータをメモリに蓄積し、最終的に CSV として書き出す。
"""

import csv
import os
import json
from datetime import datetime

import config


class DataRecorder:
    """
    実験データを蓄積・保存するクラス。
    """

    # CSV の列定義
    FIELDNAMES = [
        "subject_id",
        "sl_reference_db",
        "test_freq",
        "mod_freq",
        "mod_type",
        "masker_itd_us",
        "itd_us",
        "track",
        "trial_no",
        "session_trial_no",
        "level_db",
        "response",
        "is_reversal",
        "threshold_db",
        "reversal_levels"
    ]

    def __init__(self) -> None:
        self._rows: list[dict] = []

    def add_trial(
        self,
        subject_id: str,
        sl_reference_db: float,
        test_freq: float,
        mod_freq: float,
        mod_type: str,
        masker_itd_us: int,
        itd_us: int,
        track: str,
        trial_no: int,
        level_db: float,
        response: str,
        is_reversal: bool,
        session_trial_no: int | None = None,
    ) -> None:
        """
        1試行のデータを追加する。

        trial_no はトラック（ITD条件）内の連番、session_trial_no は
        セッション通しの連番。インターリーブ実行では後者が提示時刻を表し、
        判断基準のドリフト診断に使う。
        """
        self._rows.append({
            "subject_id": subject_id,
            "sl_reference_db": sl_reference_db,
            "test_freq": test_freq,
            "mod_freq": mod_freq,
            "mod_type": mod_type,
            "masker_itd_us": masker_itd_us,
            "itd_us": itd_us,
            "track": track,
            "trial_no": trial_no,
            "session_trial_no": session_trial_no if session_trial_no is not None else trial_no,
            "level_db": round(level_db, 2),
            "response": response,
            "is_reversal": is_reversal,
            "threshold_db": "",
            "reversal_levels": ""
        })

    def update_block_metadata(self, itd_us: int, threshold_db: float, reversal_levels: list[float]) -> None:
        """
        特定のITD条件（ブロック）に対する最終的な閾値と反転レベルのリストを、
        そのITD条件の全試行行に追記する。
        """
        rev_str = json.dumps([round(r, 2) for r in reversal_levels])
        for row in self._rows:
            if row["itd_us"] == itd_us:
                row["threshold_db"] = round(threshold_db, 4)
                row["reversal_levels"] = rev_str

    def save(self, subject_id: str) -> str:
        """
        蓄積データを CSV ファイルに書き出す。

        Parameters
        ----------
        subject_id : str

        Returns
        -------
        str
            保存した CSV のパス。
        """
        # data/ ディレクトリを作成（なければ）
        os.makedirs(config.DATA_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(config.DATA_DIR, f"{subject_id}_{timestamp}.csv")

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            writer.writerows(self._rows)

        return filename
