#!/usr/bin/env python3
"""
テスト結果を分析してJSON形式で出力するスクリプト
"""
import json
import csv
import sys
from pathlib import Path
from datetime import datetime

def analyze_positions_csv(csv_path):
    """positions.csvを分析して統計情報を返す"""
    if not Path(csv_path).exists():
        return None

    stats = {
        "total_rows": 0,
        "unique_players": set(),
        "unique_entities": set(),
        "time_range": {"start": None, "end": None},
        "teams": {"ally": 0, "enemy": 0, "neutral": 0}
    }

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["total_rows"] += 1
                if row.get("player_id") and row["player_id"] != "-1":
                    stats["unique_players"].add(row["player_id"])
                if row.get("entity_index"):
                    stats["unique_entities"].add(row["entity_index"])

                time_s = float(row.get("time_s", 0))
                if stats["time_range"]["start"] is None or time_s < stats["time_range"]["start"]:
                    stats["time_range"]["start"] = time_s
                if stats["time_range"]["end"] is None or time_s > stats["time_range"]["end"]:
                    stats["time_range"]["end"] = time_s

                side = row.get("side", "neutral")
                if side in stats["teams"]:
                    stats["teams"][side] += 1

        # setをリストに変換
        stats["unique_players"] = len(stats["unique_players"])
        stats["unique_entities"] = len(stats["unique_entities"])

        return stats
    except Exception as e:
        print(f"Error analyzing positions.csv: {e}", file=sys.stderr)
        return None

def main():
    results_file = sys.argv[1] if len(sys.argv) > 1 else "test_results.json"

    # テスト結果を読み込む
    with open(results_file, 'r') as f:
        results = json.load(f)

    # positions.csvを分析
    positions_csv = Path("d2-examples/positions.csv")
    if positions_csv.exists():
        results["positions_stats"] = analyze_positions_csv(positions_csv)

    # 結果を出力
    print(json.dumps(results, indent=2))

    # 結果をファイルに保存
    output_file = "test_results_analyzed.json"
    with open(output_file, 'w') as f:
        json.dump(results, indent=2, fp=f)

    print(f"\nAnalyzed results saved to {output_file}", file=sys.stderr)

if __name__ == "__main__":
    main()
