#!/usr/bin/env python3
"""
PRコメント用の簡易レポートを生成するスクリプト
"""
import json
import sys

def main():
    results_file = sys.argv[1] if len(sys.argv) > 1 else "test_results_analyzed.json"

    # テスト結果を読み込む
    with open(results_file, 'r') as f:
        results = json.load(f)

    # 統計を計算
    total_count = len(results.get("tests", []))
    passed_count = sum(1 for t in results.get("tests", []) if t.get("status") == "success")
    failed_count = total_count - passed_count
    total_time = sum(t.get("time", 0) for t in results.get("tests", []))

    # 全体のステータス
    overall_status = "✅ All tests passed!" if passed_count == total_count else "❌ Some tests failed"
    status_emoji = "✅" if passed_count == total_count else "❌"

    # positions統計
    positions_stats = results.get("positions_stats")
    positions_info = ""
    if positions_stats:
        positions_info = f"""
### 📊 Positions Analysis
- **Total Records**: {positions_stats.get('total_rows', 0):,}
- **Unique Players**: {positions_stats.get('unique_players', 0)}
- **Unique Entities**: {positions_stats.get('unique_entities', 0)}
"""

    # テスト結果のテーブル
    test_table = "| Test | Status | Time |\n|------|--------|------|\n"
    for test in results.get("tests", []):
        status_icon = "✅" if test.get("status") == "success" else "❌"
        test_table += f"| {test.get('name')} | {status_icon} | {test.get('time'):.2f}s |\n"

    # コメント本文を生成
    comment = f"""## {status_emoji} D2 Examples Test Report

{overall_status}

### 📈 Summary
- **Tests Passed**: {passed_count}/{total_count}
- **Tests Failed**: {failed_count}
- **Total Time**: {total_time:.2f}s

### 📋 Test Results
{test_table}
{positions_info}

---
🔗 [View detailed report](https://sunwood-ai-labs.github.io/dota2-analyzer-demo-rs/)

<sub>🤖 Generated with [Claude Code](https://claude.com/claude-code)</sub>
"""

    print(comment)

    # ファイルにも保存
    with open("pr_comment.md", 'w', encoding='utf-8') as f:
        f.write(comment)

if __name__ == "__main__":
    main()
