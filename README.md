# source2-demo

[![Test D2 Examples](https://github.com/Sunwood-ai-labs/dota2-analyzer-demo-rs/actions/workflows/test-d2-examples.yml/badge.svg)](https://github.com/Sunwood-ai-labs/dota2-analyzer-demo-rs/actions/workflows/test-d2-examples.yml)

## CI/CD

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

## Installation

Install for Dota 2 replays:

```toml
[dependencies]
source2-demo = { git = "https://github.com/Rupas1k/source2-demo", features = ["dota"] }
```

Install for Deadlock replays:

```toml
[dependencies]
source2-demo = { git = "https://github.com/Rupas1k/source2-demo", features = ["deadlock"] }
```

## Quick start

Simple program that prints chat messages from Dota 2 replay. It handles CDotaUserMsgChatMessage protobuf message and
prints player name and message text. \
More examples can be found in corresponding folders.

```rust
use source2_demo::prelude::*;
use source2_demo::proto::*;

// Create struct that implements Default trait
#[derive(Default)]
struct Chat;

// Mark impl block with observer attribute
#[observer]
impl Chat {
    #[on_message] // Use on_message attribute to mark protobuf message handler
    fn handle_chat_msg(
        &mut self,
        ctx: &Context,
        chat_msg: CDotaUserMsgChatMessage, // Use any protobuf message as an argument (CDotaUserMsgChatMessage in this case)
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
    // Read replay file
    let replay = unsafe { memmap2::Mmap::map(&std::fs::File::open("replay.dem")?)? };

    // Create parser 
    let mut parser = Parser::new(&replay)?;

    // Register observers
    parser.register_observer::<Chat>();

    // Run it!
    parser.run_to_end()?;

    Ok(())
}

```

## Build examples

```shell
git clone https://github.com/Rupas1k/source2-demo
cd source2-demo/dl-examples # cd source2-demo/d2-examples
cargo build --release
```
