# dota2-analyzer-demo-rs

[![Test D2 Examples](https://github.com/Sunwood-ai-labs/dota2-analyzer-demo-rs/actions/workflows/test-d2-examples.yml/badge.svg)](https://github.com/Sunwood-ai-labs/dota2-analyzer-demo-rs/actions/workflows/test-d2-examples.yml)

Dota 2のリプレイファイル（.demファイル）を解析するためのRustライブラリおよびサンプル集です。Source 2エンジンのデモファイルフォーマットをパースし、ゲーム内の様々なイベントやエンティティ情報を抽出できます。

## 特徴

- **高速パース**: Rustによる高速なリプレイファイル解析
- **豊富なサンプル**: チャット、位置情報、戦闘ログ、ワード配置など、実用的なサンプルコードを多数収録
- **型安全**: Rustの型システムによる安全なデータ処理
- **拡張可能**: Observerパターンにより、独自の解析ロジックを簡単に追加可能
- **Deadlock対応**: Dota 2だけでなくDeadlockのリプレイにも対応

## 📦 プロジェクト構成

このリポジトリは以下のコンポーネントで構成されています：

- **source2-demo**: メインライブラリ（パーサー、エンティティ、イベントシステム）
- **source2-demo-protobufs**: Protocol Buffersの定義とコード生成
- **source2-demo-macros**: Observerパターンを実現するマクロ
- **d2-examples**: Dota 2向けの実用的なサンプルコード集
  - `chat`: チャットメッセージの抽出
  - `positions`: プレイヤー/ヒーローの位置情報をCSV出力
  - `combatlog`: 戦闘ログの解析
  - `lifestate`: ユニットの生存状態の追跡
  - `wards`: ワードの配置情報の抽出

## 🚀 インストール

Dota 2のリプレイを解析する場合：

```toml
[dependencies]
source2-demo = { git = "https://github.com/Rupas1k/source2-demo", features = ["dota"] }
```

Deadlockのリプレイを解析する場合：

```toml
[dependencies]
source2-demo = { git = "https://github.com/Rupas1k/source2-demo", features = ["deadlock"] }
```

## 📖 クイックスタート

Dota 2のリプレイからチャットメッセージを抽出する簡単なプログラムです。`CDotaUserMsgChatMessage`プロトコルバッファメッセージを処理し、プレイヤー名とメッセージ内容を出力します。

```rust
use source2_demo::prelude::*;
use source2_demo::proto::*;

// Defaultトレイトを実装した構造体を作成
#[derive(Default)]
struct Chat;

// observer属性をimplブロックに付与
#[observer]
impl Chat {
    #[on_message] // プロトコルバッファメッセージハンドラを示す属性
    fn handle_chat_msg(
        &mut self,
        ctx: &Context,
        chat_msg: CDotaUserMsgChatMessage, // 任意のプロトコルバッファメッセージを引数に使用可能
    ) -> ObserverResult {
        if let Ok(pr) = ctx.entities().get_by_class_name("CDOTA_PlayerResource") {
            let name: String = property!(
                pr,
                "m_vecPlayerData.{:04}.m_iszPlayerName",
                chat_msg.source_player_id()
            );
            println!("{}: {}", name, chat_msg.message_text());
        }
        Ok(())
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // リプレイファイルを読み込み
    let replay = unsafe { memmap2::Mmap::map(&std::fs::File::open("replay.dem")?)? };

    // パーサーを作成
    let mut parser = Parser::new(&replay)?;

    // Observerを登録
    parser.register_observer::<Chat>();

    // 実行！
    parser.run_to_end()?;

    Ok(())
}
```

## 🔨 サンプルのビルドと実行

```shell
# リポジトリをクローン
git clone https://github.com/Sunwood-ai-labs/dota2-analyzer-demo-rs
cd dota2-analyzer-demo-rs/d2-examples

# ビルド
cargo build --release

# サンプルの実行例
./target/release/chat your_replay.dem
./target/release/positions your_replay.dem
./target/release/combatlog your_replay.dem
```

### 位置情報の解析例

位置情報サンプルは、プレイヤー視点（Radiant/Dire）を指定できます：

```shell
# Radiant視点で解析（デフォルト）
./target/release/positions replay.dem

# Dire視点で解析
./target/release/positions replay.dem --pov=dire
```

出力されたCSVファイルには以下の情報が含まれます：
- タイムスタンプ（秒）
- ティック番号
- エンティティインデックス
- チーム番号
- プレイヤーID
- プレイヤー名
- 敵味方の判定（ally/enemy/neutral）
- 3D座標（x, y, z）
- エンティティクラス名

## 🤖 CI/CD

このリポジトリには、d2-examplesの動作を確認するための自動テストとレポート生成システムが設定されています。

### 📊 機能

- **自動テスト**: 全てのd2-examplesを自動的にテスト
- **HTMLレポート**: [GitHub Pages](https://sunwood-ai-labs.github.io/dota2-analyzer-demo-rs/report.html)で詳細なテスト結果を公開
- **PRコメント**: Pull Requestに自動的にテスト結果を追加
- **統計分析**: positions.csvから詳細な統計情報を抽出
- **実行時間計測**: 各サンプルのパフォーマンス測定

### 🔧 設定

- **ワークフロー**: `.github/workflows/test-d2-examples.yml`
- **テストデモファイル**: [HuggingFace: dota2-sample-dem](https://huggingface.co/datasets/MakiAi/dota2-sample-dem/blob/main/auto-20251019-2017-start-maki.dem)
- **テスト対象**: chat, positions, combatlog, lifestate, wards

### 📈 レポート

- **詳細レポート**: mainブランチにpushすると、[GitHub Pages](https://sunwood-ai-labs.github.io/dota2-analyzer-demo-rs/report.html)に自動デプロイ
- **PRコメント**: Pull Requestには簡易的なテスト結果を自動コメント

すべてのサンプルがデモファイルで正しく動作することを自動的に確認します。

## 📚 サンプル詳細

### chat
リプレイファイルからチャットメッセージを抽出し、プレイヤー名とメッセージを表示します。

### positions
ゲーム中のプレイヤー/ヒーローの位置情報をティックごとにCSVファイルに出力します。視覚化やヒートマップ生成に活用できます。

### combatlog
戦闘ログ（キル、ダメージ、アビリティ使用など）を解析します。

### lifestate
ユニットの生存状態（生存、死亡、リスポーン）を追跡します。

### wards
オブザーバーワードやセントリーワードの配置情報を抽出します。

## 🔗 関連リンク

- [元のsource2-demoリポジトリ](https://github.com/Rupas1k/source2-demo)
- [テストレポート（GitHub Pages）](https://sunwood-ai-labs.github.io/dota2-analyzer-demo-rs/report.html)
- [サンプルデモファイル（HuggingFace）](https://huggingface.co/datasets/MakiAi/dota2-sample-dem)

## 📄 ライセンス

このプロジェクトはMITライセンスまたはApache-2.0ライセンスのデュアルライセンスです。
