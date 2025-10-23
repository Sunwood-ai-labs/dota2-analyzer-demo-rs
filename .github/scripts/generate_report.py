#!/usr/bin/env python3
"""
テスト結果からHTMLレポートを生成するスクリプト
テンプレートファイルを使用してプレースホルダーを置換
"""
import json
import sys
from datetime import datetime
from pathlib import Path

def load_template(template_name):
    """テンプレートファイルを読み込む"""
    template_dir = Path(__file__).parent / "templates"
    template_path = template_dir / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_test_item(test, test_item_template):
    """テスト項目のHTMLを生成"""
    status = test.get("status")
    status_class = "success" if status == "success" else "failed"
    status_icon = "✓" if status == "success" else "✗"

    replacements = {
        "{{STATUS_CLASS}}": status_class,
        "{{STATUS_ICON}}": status_icon,
        "{{TEST_NAME}}": test.get("name"),
        "{{TEST_TIME}}": f"{test.get('time'):.2f}",
        "{{STATUS_UPPER}}": status.upper()
    }

    html = test_item_template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html

def generate_positions_section(positions_stats, positions_template):
    """positions.csvの統計セクションを生成"""
    if not positions_stats:
        return ""

    duration = positions_stats.get("time_range", {}).get("end", 0) - \
               positions_stats.get("time_range", {}).get("start", 0)

    replacements = {
        "{{TOTAL_ROWS}}": f"{positions_stats.get('total_rows', 0):,}",
        "{{UNIQUE_PLAYERS}}": str(positions_stats.get("unique_players", 0)),
        "{{DURATION}}": f"{duration:.1f}",
        "{{UNIQUE_ENTITIES}}": str(positions_stats.get("unique_entities", 0))
    }

    html = positions_template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html

def main():
    results_file = sys.argv[1] if len(sys.argv) > 1 else "test_results_analyzed.json"

    # テスト結果を読み込む
    with open(results_file, 'r') as f:
        results = json.load(f)

    # テンプレートを読み込む
    main_template = load_template("report_template.html")
    test_item_template = load_template("test_item.html")
    positions_template = load_template("positions_section.html")

    # 統計を計算
    total_count = len(results.get("tests", []))
    passed_count = sum(1 for t in results.get("tests", []) if t.get("status") == "success")
    total_time = sum(t.get("time", 0) for t in results.get("tests", []))
    overall_status = "✓ PASSED" if passed_count == total_count else "✗ FAILED"
    overall_status_class = "success" if passed_count == total_count else "warning"

    # テスト項目のHTMLを生成
    test_items = "\n".join([
        generate_test_item(test, test_item_template)
        for test in results.get("tests", [])
    ])

    # positions統計
    positions_stats = results.get("positions_stats")
    positions_section = generate_positions_section(positions_stats, positions_template)
    data_points = positions_stats.get("total_rows", 0) if positions_stats else 0

    # Chart.js用のデータ
    time_data = {
        "labels": [t.get("name") for t in results.get("tests", [])],
        "values": [t.get("time") for t in results.get("tests", [])]
    }

    # プレースホルダーを置換
    replacements = {
        "{{TIMESTAMP}}": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "{{OVERALL_STATUS}}": overall_status,
        "{{OVERALL_STATUS_CLASS}}": overall_status_class,
        "{{PASSED_COUNT}}": str(passed_count),
        "{{TOTAL_COUNT}}": str(total_count),
        "{{TOTAL_TIME}}": f"{total_time:.2f}",
        "{{DATA_POINTS}}": f"{data_points:,}",
        "{{TEST_ITEMS}}": test_items,
        "{{POSITIONS_SECTION}}": positions_section,
        "{{TIME_DATA}}": json.dumps(time_data)
    }

    html = main_template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # HTMLファイルを保存
    output_file = "report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Report generated: {output_file}")

if __name__ == "__main__":
    main()
