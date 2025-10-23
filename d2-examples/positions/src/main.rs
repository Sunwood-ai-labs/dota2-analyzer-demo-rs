use source2_demo::prelude::*;
use std::collections::BTreeSet;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::PathBuf;

struct Positions {
    heroes: BTreeSet<u32>,
    out: Option<BufWriter<File>>,
    initialized: bool,
    // 視点チーム（2: Radiant, 3: Dire）
    pov_team: i32,
    // CSV の出力先
    out_path: PathBuf,
}

impl Default for Positions {
    fn default() -> Self {
        Self {
            heroes: BTreeSet::new(),
            out: None,
            initialized: false,
            // Radiant をデフォルト視点に
            pov_team: 2,
            out_path: PathBuf::from("viz/hero_stats.csv"),
        }
    }
}

impl Positions {
    fn player_stat_i32(pr: &Entity, pid: i32, keys: &[&str]) -> Option<i32> {
        for key in keys {
            let formatted = if key.contains("{:04}") {
                key.replace("{:04}", &format!("{pid:04}"))
            } else if key.contains("{}") {
                key.replace("{}", &pid.to_string())
            } else {
                key.to_string()
            };
            if let Ok(prop) = pr.get_property_by_name(&formatted) {
                if let Ok(value) = prop.try_into() {
                    return Some(value);
                }
            }
        }
        None
    }

    fn sanitize_field(value: &str) -> String {
        value
            .replace(',', " ")
            .replace('\n', " ")
            .replace('\r', " ")
            .trim()
            .to_string()
    }
}

#[observer]
impl Positions {
    #[on_entity]
    fn on_entity(&mut self, _ctx: &Context, ev: EntityEvents, e: &Entity) -> ObserverResult {
        // ヒーロー/プレイヤブルユニット推定: m_iPlayerID を持つエンティティ
        let has_player_id = e.get_property_by_name("m_iPlayerID").is_ok();
        match ev {
            EntityEvents::Created | EntityEvents::Updated => {
                if has_player_id {
                    self.heroes.insert(e.index());
                }
            }
            EntityEvents::Deleted => {
                self.heroes.remove(&e.index());
            }
        }
        Ok(())
    }

    #[on_tick_end]
    fn on_tick_end(&mut self, ctx: &Context) -> ObserverResult {
        if self.out.is_none() {
            if let Some(parent) = self.out_path.parent() {
                if !parent.as_os_str().is_empty() {
                    std::fs::create_dir_all(parent)?;
                }
            }
            let f = File::create(&self.out_path)?;
            let mut w = BufWriter::new(f);
            writeln!(
                w,
                "time_s,tick,entity_index,team,player_id,player_name,side,level,current_xp,total_xp,reliable_gold,unreliable_gold,total_gold,net_worth,gpm,xpm,health,max_health,mana,max_mana,x,y,z,class"
            )?;
            self.out = Some(w);
        }
        let Some(out) = self.out.as_mut() else {
            return Ok(());
        };

        if !self.initialized {
            for e in ctx.entities().iter() {
                if e.get_property_by_name("m_iPlayerID").is_ok() {
                    self.heroes.insert(e.index());
                }
            }
            self.initialized = true;
        }

        // Dota2 は 30 tick/秒
        let tick = ctx.tick();
        let time_s = tick as f32 / 30.0;

        let player_resource = ctx
            .entities()
            .get_by_class_name("CDOTA_PlayerResource")
            .ok();

        for &idx in &self.heroes {
            let entity = match ctx.entities().get_by_index(idx as usize) {
                Ok(ent) => ent,
                Err(_) => continue,
            };

            let team: Option<i32> = entity
                .get_property_by_name("m_iTeamNum")
                .ok()
                .and_then(|p| p.try_into().ok());
            let player_id: Option<i32> = entity
                .get_property_by_name("m_iPlayerID")
                .ok()
                .and_then(|p| p.try_into().ok());

            let player_name = if let (Some(pr), Some(pid)) = (player_resource, player_id) {
                try_property!(pr, String, "m_vecPlayerData.{:04}.m_iszPlayerName", pid)
                    .unwrap_or_default()
            } else {
                String::new()
            };
            let player_name = Positions::sanitize_field(&player_name);

            // 位置プロパティのフォールバック（m_vecOrigin → CBodyComponent.m_vecOrigin）
            let x_origin: Option<f32> = entity
                .get_property_by_name("m_vecOrigin[0]")
                .ok()
                .and_then(|p| p.try_into().ok());
            let y_origin: Option<f32> = entity
                .get_property_by_name("m_vecOrigin[1]")
                .ok()
                .and_then(|p| p.try_into().ok());
            let z_origin: Option<f32> = entity
                .get_property_by_name("m_vecOrigin[2]")
                .ok()
                .and_then(|p| p.try_into().ok());

            let (mut x, mut y, mut z) = (x_origin, y_origin, z_origin);
            if x.is_none() && y.is_none() {
                const CELL_SIZE: f32 = 128.0;
                let cx: Option<i32> = entity
                    .get_property_by_name("CBodyComponent.m_cellX")
                    .ok()
                    .and_then(|p| p.try_into().ok());
                let cy: Option<i32> = entity
                    .get_property_by_name("CBodyComponent.m_cellY")
                    .ok()
                    .and_then(|p| p.try_into().ok());
                let cz: Option<i32> = entity
                    .get_property_by_name("CBodyComponent.m_cellZ")
                    .ok()
                    .and_then(|p| p.try_into().ok());
                let vx: Option<f32> = entity
                    .get_property_by_name("CBodyComponent.m_vecX")
                    .ok()
                    .and_then(|p| p.try_into().ok());
                let vy: Option<f32> = entity
                    .get_property_by_name("CBodyComponent.m_vecY")
                    .ok()
                    .and_then(|p| p.try_into().ok());
                let vz: Option<f32> = entity
                    .get_property_by_name("CBodyComponent.m_vecZ")
                    .ok()
                    .and_then(|p| p.try_into().ok());

                if let (Some(cx), Some(vx)) = (cx, vx) {
                    x = Some(cx as f32 * CELL_SIZE + vx);
                }
                if let (Some(cy), Some(vy)) = (cy, vy) {
                    y = Some(cy as f32 * CELL_SIZE + vy);
                }
                if let (Some(cz), Some(vz)) = (cz, vz) {
                    z = Some(cz as f32 * CELL_SIZE + vz);
                }
            }

            let class = Positions::sanitize_field(entity.class().name());

            let level = try_property!(entity, i32, "m_iCurrentLevel").unwrap_or(-1);
            let current_xp = try_property!(entity, i32, "m_iCurrentXP").unwrap_or(-1);
            let health = try_property!(entity, i32, "m_iHealth").unwrap_or(-1);
            let max_health = try_property!(entity, i32, "m_iMaxHealth").unwrap_or(-1);
            let mana = try_property!(entity, f32, "m_flMana").unwrap_or(-1.0);
            let max_mana = try_property!(entity, f32, "m_flMaxMana").unwrap_or(-1.0);

            const TOTAL_XP_KEYS: [&str; 2] = [
                "m_vecPlayerTeamData.{:04}.m_iTotalEarnedXP",
                "m_vecPlayerData.{:04}.m_iTotalEarnedXP",
            ];
            const RELIABLE_GOLD_KEYS: [&str; 2] = [
                "m_vecPlayerTeamData.{:04}.m_iReliableGold",
                "m_vecPlayerData.{:04}.m_iReliableGold",
            ];
            const UNRELIABLE_GOLD_KEYS: [&str; 2] = [
                "m_vecPlayerTeamData.{:04}.m_iUnreliableGold",
                "m_vecPlayerData.{:04}.m_iUnreliableGold",
            ];
            const TOTAL_GOLD_KEYS: [&str; 2] = [
                "m_vecPlayerTeamData.{:04}.m_iTotalEarnedGold",
                "m_vecPlayerData.{:04}.m_iTotalEarnedGold",
            ];
            const NET_WORTH_KEYS: [&str; 2] = [
                "m_vecPlayerTeamData.{:04}.m_iNetWorth",
                "m_vecPlayerData.{:04}.m_iNetWorth",
            ];

            let get_stat = |keys: &[&str]| -> i32 {
                if let (Some(pr), Some(pid)) = (player_resource, player_id) {
                    Positions::player_stat_i32(pr, pid, keys).unwrap_or(-1)
                } else {
                    -1
                }
            };

            let total_xp = get_stat(&TOTAL_XP_KEYS);
            let reliable_gold = get_stat(&RELIABLE_GOLD_KEYS);
            let unreliable_gold = get_stat(&UNRELIABLE_GOLD_KEYS);
            let total_gold = get_stat(&TOTAL_GOLD_KEYS);
            let mut net_worth = get_stat(&NET_WORTH_KEYS);
            if net_worth < 0 {
                net_worth = [reliable_gold, unreliable_gold]
                    .into_iter()
                    .filter(|v| *v >= 0)
                    .sum::<i32>();
            }

            let gpm = if total_gold >= 0 && time_s > f32::EPSILON {
                (total_gold as f32) / (time_s / 60.0)
            } else {
                -1.0
            };
            let xpm = if total_xp >= 0 && time_s > f32::EPSILON {
                (total_xp as f32) / (time_s / 60.0)
            } else {
                -1.0
            };

            let side = match team.unwrap_or(-1) {
                t if t == self.pov_team => "ally".to_string(),
                2 | 3 => "enemy".to_string(),
                _ => "neutral".to_string(),
            };

            writeln!(
                out,
                "{:.3},{},{},{},{},{},{},{},{},{},{},{},{},{},{:.1},{:.1},{},{},{:.1},{:.1},{:.3},{:.3},{:.3},{}",
                time_s,
                tick,
                idx,
                team.unwrap_or(-1),
                player_id.unwrap_or(-1),
                player_name,
                side,
                level,
                current_xp,
                total_xp,
                reliable_gold,
                unreliable_gold,
                total_gold,
                net_worth,
                gpm,
                xpm,
                health,
                max_health,
                mana,
                max_mana,
                x.unwrap_or(0.0),
                y.unwrap_or(0.0),
                z.unwrap_or(0.0),
                class
            )?;
        }

        Ok(())
    }

    #[on_stop]
    fn on_stop(&mut self, _ctx: &Context) -> ObserverResult {
        if let Some(out) = self.out.as_mut() {
            out.flush()?;
        }
        Ok(())
    }
}

fn main() -> anyhow::Result<()> {
    let args = std::env::args().collect::<Vec<_>>();
    let Some(filepath) = args.get(1) else {
        eprintln!(
            "Usage: {} <demofile> [--pov=2|3|radiant|dire] [--out=stats.csv]\n       (default output: viz/hero_stats.csv)",
            args[0]
        );
        return Ok(());
    };

    let replay = unsafe { memmap2::Mmap::map(&std::fs::File::open(filepath)?)? };
    let mut parser = Parser::new(&replay)?;

    let positions = parser.register_observer::<Positions>();

    let mut pov_team: i32 = 2;
    let mut out_path: Option<String> = None;
    for arg in &args[2..] {
        if let Some(rest) = arg.strip_prefix("--pov=") {
            pov_team = match rest.to_ascii_lowercase().as_str() {
                "2" | "radiant" | "goodguys" => 2,
                "3" | "dire" | "badguys" => 3,
                _ => 2,
            };
        } else if let Some(rest) = arg.strip_prefix("--out=") {
            out_path = Some(rest.to_string());
        }
    }

    {
        let mut pos = positions.borrow_mut();
        pos.pov_team = pov_team;
        if let Some(path) = out_path {
            pos.out_path = PathBuf::from(path);
        }
    }

    let start = std::time::Instant::now();
    parser.run_to_end()?;
    println!("Elapsed: {:?}", start.elapsed());

    Ok(())
}
