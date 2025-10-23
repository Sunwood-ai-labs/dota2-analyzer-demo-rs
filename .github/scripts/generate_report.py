#!/usr/bin/env python3
"""
テスト結果からHTMLレポートを生成するスクリプト
"""
import json
import sys
from datetime import datetime
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D2 Examples Test Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        .content {{
            padding: 2rem;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card.success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-card.warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .stat-card h3 {{
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 2rem;
            font-weight: bold;
        }}
        .section {{
            margin-bottom: 2rem;
        }}
        .section h2 {{
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.5rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
        }}
        .test-results {{
            display: grid;
            gap: 1rem;
        }}
        .test-item {{
            display: flex;
            align-items: center;
            padding: 1rem;
            background: #f7fafc;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}
        .test-item.success {{ border-left-color: #38ef7d; }}
        .test-item.failed {{ border-left-color: #f5576c; }}
        .test-item .status {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 1rem;
            font-weight: bold;
        }}
        .test-item.success .status {{
            background: #38ef7d;
            color: white;
        }}
        .test-item.failed .status {{
            background: #f5576c;
            color: white;
        }}
        .test-item .info {{
            flex: 1;
        }}
        .test-item .name {{
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}
        .test-item .time {{
            color: #718096;
            font-size: 0.875rem;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
            margin: 1rem 0;
        }}
        .footer {{
            text-align: center;
            padding: 1.5rem;
            color: #718096;
            background: #f7fafc;
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }}
        .badge.success {{ background: #c6f6d5; color: #22543d; }}
        .badge.failed {{ background: #fed7d7; color: #742a2a; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 D2 Examples Test Report</h1>
            <p>Automated testing results for Dota 2 demo file analysis</p>
            <p style="margin-top: 1rem; font-size: 0.9rem;">Generated: {timestamp}</p>
        </div>

        <div class="content">
            <div class="summary">
                <div class="stat-card {overall_status_class}">
                    <h3>Overall Status</h3>
                    <div class="value">{overall_status}</div>
                </div>
                <div class="stat-card">
                    <h3>Tests Passed</h3>
                    <div class="value">{passed_count}/{total_count}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Time</h3>
                    <div class="value">{total_time}s</div>
                </div>
                <div class="stat-card">
                    <h3>Data Points</h3>
                    <div class="value">{data_points}</div>
                </div>
            </div>

            <div class="section">
                <h2>📋 Test Results</h2>
                <div class="test-results">
                    {test_items}
                </div>
            </div>

            {positions_section}

            <div class="section">
                <h2>📊 Execution Time</h2>
                <div class="chart-container">
                    <canvas id="timeChart"></canvas>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>🤖 Generated with <a href="https://claude.com/claude-code" style="color: #667eea;">Claude Code</a></p>
            <p style="margin-top: 0.5rem;">
                <a href="https://github.com/Sunwood-ai-labs/dota2-analyzer-demo-rs" style="color: #667eea;">View Repository</a>
            </p>
        </div>
    </div>

    <script>
        const timeData = {time_data};

        const ctx = document.getElementById('timeChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: timeData.labels,
                datasets: [{{
                    label: 'Execution Time (seconds)',
                    data: timeData.values,
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(118, 75, 162, 0.8)',
                        'rgba(17, 153, 142, 0.8)',
                        'rgba(56, 239, 125, 0.8)',
                        'rgba(240, 147, 251, 0.8)'
                    ],
                    borderColor: [
                        'rgba(102, 126, 234, 1)',
                        'rgba(118, 75, 162, 1)',
                        'rgba(17, 153, 142, 1)',
                        'rgba(56, 239, 125, 1)',
                        'rgba(240, 147, 251, 1)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Seconds'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

def generate_test_item(name, status, time):
    """テスト項目のHTMLを生成"""
    status_class = "success" if status == "success" else "failed"
    status_icon = "✓" if status == "success" else "✗"

    return f"""
    <div class="test-item {status_class}">
        <div class="status">{status_icon}</div>
        <div class="info">
            <div class="name">{name}</div>
            <div class="time">Execution time: {time}s</div>
        </div>
        <span class="badge {status_class}">{status.upper()}</span>
    </div>
    """

def generate_positions_section(positions_stats):
    """positions.csvの統計セクションを生成"""
    if not positions_stats:
        return ""

    duration = positions_stats.get("time_range", {}).get("end", 0) - positions_stats.get("time_range", {}).get("start", 0)

    return f"""
    <div class="section">
        <h2>🗺️ Positions Analysis</h2>
        <div class="summary">
            <div class="stat-card">
                <h3>Total Records</h3>
                <div class="value">{positions_stats.get("total_rows", 0):,}</div>
            </div>
            <div class="stat-card">
                <h3>Unique Players</h3>
                <div class="value">{positions_stats.get("unique_players", 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Duration</h3>
                <div class="value">{duration:.1f}s</div>
            </div>
            <div class="stat-card">
                <h3>Unique Entities</h3>
                <div class="value">{positions_stats.get("unique_entities", 0)}</div>
            </div>
        </div>
    </div>
    """

def main():
    results_file = sys.argv[1] if len(sys.argv) > 1 else "test_results_analyzed.json"

    # テスト結果を読み込む
    with open(results_file, 'r') as f:
        results = json.load(f)

    # 統計を計算
    total_count = len(results.get("tests", []))
    passed_count = sum(1 for t in results.get("tests", []) if t.get("status") == "success")
    total_time = sum(t.get("time", 0) for t in results.get("tests", []))
    overall_status = "✓ PASSED" if passed_count == total_count else "✗ FAILED"
    overall_status_class = "success" if passed_count == total_count else "warning"

    # テスト項目のHTMLを生成
    test_items = "\n".join([
        generate_test_item(t.get("name"), t.get("status"), t.get("time"))
        for t in results.get("tests", [])
    ])

    # positions統計
    positions_stats = results.get("positions_stats")
    positions_section = generate_positions_section(positions_stats)
    data_points = positions_stats.get("total_rows", 0) if positions_stats else 0

    # Chart.js用のデータ
    time_data = {
        "labels": [t.get("name") for t in results.get("tests", [])],
        "values": [t.get("time") for t in results.get("tests", [])]
    }

    # HTMLを生成
    html = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        overall_status=overall_status,
        overall_status_class=overall_status_class,
        passed_count=passed_count,
        total_count=total_count,
        total_time=f"{total_time:.2f}",
        data_points=f"{data_points:,}",
        test_items=test_items,
        positions_section=positions_section,
        time_data=json.dumps(time_data)
    )

    # HTMLファイルを保存
    output_file = "report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Report generated: {output_file}")

if __name__ == "__main__":
    main()
