# ncmWS — 网易云音乐歌单爬虫

抓取指定歌单下所有歌曲的基本信息（歌曲名称、时长、歌手、专辑及各类 ID），并补充每首歌的**语种**与**歌曲类型**，最终输出两份 CSV。

- 目标歌单：<https://music.163.com/playlist?id=565910665>（鸿日虹桥红谷滩喜欢的音乐）
- 任务说明：[task.md](task.md)

## 项目结构

```
ncmWS/
├── task.md                  # 任务说明
├── README.md
├── src/
│   ├── ncm_common.py        # 公共配置：会话、Cookie、时长格式化等
│   ├── get_cookie.py        # 扫码登录并保存 Cookie（阶段2需要）
│   ├── step1_playlist.py    # 阶段1：歌单基本信息
│   ├── step2_wiki.py        # 阶段2：语种与歌曲类型
│   └── step3_merge.py       # 阶段3：汇总输出两份 CSV
├── genre_testset/           # 七流派测试集（见下文「七流派测试集」）
│   ├── src/
│   │   ├── build_testset.py # 按给定歌单抓取 + 类型校验 + 分类补足
│   │   └── fetch_blues.py   # 旧版蓝调艺人补充脚本（已弃用，保留备查）
│   ├── data/
│   │   ├── testset_{genre}.csv   # 分流派数据，每类 100 首
│   │   ├── testset_all.csv       # 七类汇总
│   │   ├── testset_summary.csv   # 抓取统计
│   │   └── raw/                  # 接口缓存（本地生成，不入库）
│   └── skipped_songs.md          # 各类别被跳过的曲目位置与原因
└── data/
    ├── step1_playlist.csv       # 阶段1 中间结果
    ├── step2_style.csv          # 阶段2 中间结果
    ├── ncm_songs_all_info.csv   # 阶段3 全部信息
    ├── ncm_songs_key_info.csv   # 阶段3 关键信息
    ├── cookies.json             # 登录 Cookie（本地生成，不入库）
    └── raw/                     # 原生数据与缓存（本地生成，不入库）
        ├── playlist_page.html
        ├── playlist_detail.json
        ├── song_detail.json
        └── wiki/album_{album_id}.json
```

## 环境依赖

- Python 3.10+
- `requests`
- `playwright`（仅阶段 2 获取登录 Cookie 时需要）

```bash
pip install requests playwright
python -m playwright install chromium
```

## 使用步骤

### 阶段 1：歌单基本信息

```bash
python src/step1_playlist.py            # 全量
python src/step1_playlist.py --limit 50 # 仅前 50 首（验证）
```

抓取歌单页面、歌单详情与全部歌曲详情，原生数据写入 `data/raw/`，有效数据写入 `data/step1_playlist.csv`。

### 阶段 2：语种与歌曲类型

网易云旧版 wiki 页面（`/wiki/album?albumId=…`）现已下线，其数据由「音乐百科」UGC 接口提供且**需要登录**（未登录返回 `code=301`，前端跳转登录页）。因此先扫码登录：

```bash
python src/get_cookie.py    # 弹出浏览器，扫码登录后自动保存 data/cookies.json
```

再执行：

```bash
python src/step2_wiki.py --limit 50     # 先验证
python src/step2_wiki.py --workers 4    # 全量，多线程预取专辑数据
```

处理逻辑：

1. 用 song id / album id 构造 wiki URL：
   - `https://music.163.com/#/wiki/album?albumId={album_id}`
   - `https://music.163.com/#/wiki/song?songId={song_id}&type=1`
2. 按 album id 拉取专辑内全部歌曲信息，按歌曲名称匹配目标歌曲（同名用 songId 消歧），取 `language`（语种）与 `songTags`（歌曲类型）；
3. 专辑级数据缺失时回退歌曲级接口；
4. 专辑原始响应缓存到 `data/raw/wiki/`，重复运行自动跳过已缓存数据（可断点续跑）。

### 阶段 3：汇总输出

```bash
python src/step3_merge.py
```

按 song id 合并阶段 1、阶段 2 结果，输出两份 CSV。

## 输出文件

### `data/ncm_songs_all_info.csv` — 全部信息

| 字段 | 说明 |
| --- | --- |
| 序号 | 歌单内顺序 |
| 歌曲名称 | |
| song id | 网易云歌曲 ID |
| 总时长 | `mm:ss` |
| 歌手 | 多歌手用 ` / ` 分隔 |
| artist id | 多歌手 ID 用 ` / ` 分隔 |
| 专辑 | |
| album id | |
| 语种 | 来自音乐百科，如 英语 / 国语 / 粤语 / 日语 / 纯音乐 |
| 歌曲类型 | 来自音乐百科，多个类型用 ` / ` 分隔，如 流行 / R&B |

### `data/ncm_songs_key_info.csv` — 关键信息

`歌曲名称, 时长, 歌手, 专辑, 语种, 歌曲类型`

## 数据统计（当前结果）

- 歌曲：2769 首，覆盖 2489 张专辑
- 语种与歌曲类型：2759 首成功获取（99.6%）
- 语种分布：英语 1540、纯音乐 562、国语 359、日语 120、华语 55、粤语 48 …
- 类型分布：流行 906、电子 817、摇滚 393、嘻哈说唱 345、原声带 166、R&B 162 …

## 七流派测试集（genre_testset）

为音乐流派识别任务构建的平衡测试集：blues / classical / country / hiphop / jazz / pop / rock 七类各 **100 首**，合计 **700 首**。

### 数据来源歌单

| 流派 | 歌单 | 歌单 id | 补充/候补歌单 | 歌单 id | 补充曲目数 |
| --- | --- | --- | --- | --- | --- |
| blues | 100blues大师-布鲁斯是他们的生命 | 102463641 | 蓝调悠闲馆 \| 一杯蓝调 半日闲情 | 14274068640 | 31 |
| classical | 世界级古典钢琴曲音乐珍藏 | 167900089 | 古典造梦机 \| 跌进柔软梦中 纵享迷人韵律 | 8621500200 | 6 |
| country | 美国乡村民谣之旅 | 697173945 | 乡村乐 \| 在音乐中暂别城市·杜比全景声 | 8282791588 | 50 |
| hiphop | hiphop炸曲神曲大整合 dancer必备！ | 439484002 | —（无需补充） | — | 0 |
| jazz | 爵士小情歌 \| 同慵懒爵士缠绵悱恻 | 2829895462 | —（无需补充） | — | 0 |
| pop | 我喜欢的音乐-流行 | 18639172099 | —（无需补充） | — | 0 |
| rock | 史上最伟大的100首摇滚歌曲 | 8240950353 | 欧美摇滚经典（候补歌单） | 722234258 | 16 |

说明：blues / classical / country 的补充歌单取自网易云对应分类的热门歌单榜（各只用到第 1 个即凑满 100 首）；rock 的候补来源为上述指定歌单。

### 抓取规则

1. 按给定歌单的**原始顺序**逐首扫描，用专辑音乐百科的「歌曲类型」标签校验是否包含目标流派（如 blues 必须含「蓝调」）；
2. 校验音源可用性：调用播放地址接口，返回 `url` 为空（`code=404`）的曲目视为**无音源、无法下载**，即使歌单里仍在、详情页可访问也一并剔除；
3. 类型不符或无音源的曲目**跳过并继续往后取**，直到该类别收满 100 首；
4. 给定歌单扫完仍不足 100 首时：blues / classical / country 从网易云对应分类的热门歌单依次补充；rock 从指定候补歌单「欧美摇滚经典」（722234258）补充，且候补时**同一歌手最多收录 1 首**；
5. 跨歌单按 song id 与歌名去重，候补歌单中与前面歌单重复的曲目**跳过并顺延**；
6. 补充/候补曲目同样逐首校验类型标签与音源。

各类别具体跳过了歌单中的第几首、以及跳过原因（含候补歌单中被跳过的曲目），见 [genre_testset/skipped_songs.md](genre_testset/skipped_songs.md)。

### 运行

复用主项目的登录 Cookie（`data/cookies.json`），语种/类型标签与播放地址均取自需要登录的接口：

```bash
python genre_testset/src/build_testset.py                 # 默认每类 100 首
python genre_testset/src/build_testset.py --target 50     # 验证用，只取 50 首
python genre_testset/src/build_testset.py --genre pop     # 只重建指定类别，其余沿用原 CSV
python genre_testset/src/build_testset.py --no-url-check  # 关闭音源过滤（保留无音源曲目）
```

接口缓存写入 `genre_testset/data/raw/`（含 `song_url_*.json` 音源检查结果，已加入 `.gitignore`），重跑自动复用，可断点续跑；删除缓存即可完全重抓。

### 输出文件

- `genre_testset/data/testset_{genre}.csv`：分流派数据，每类 100 行
- `genre_testset/data/testset_all.csv`：七类汇总，700 行
- `genre_testset/data/testset_summary.csv`：各类抓取统计
- `genre_testset/skipped_songs.md`：各流派在给定歌单中被跳过的曲目位置与原因

字段：`序号, 歌曲名称, song id, 总时长, 歌手, artist id, 专辑, album id, 语种, 歌曲类型, 歌曲类型_en, genre, 歌单位置, 数据来源`

其中 `歌曲类型_en` 为中文类型标签的英文映射（如 `流行 / 摇滚` → `pop / rock`），`歌单位置` 为曲目在来源歌单中的序号（候补曲目为在候补歌单内的序号），`数据来源` 为 `given_playlist`、`supplement_playlist:{歌单id}` 或 `fallback_playlist:{歌单id}`。

### 抓取统计

| 流派 | 给定歌单曲目数 | 扫描曲目数 | 命中 | 类型不符 | 无音源 | 补充歌单 | 补充曲目 | 满额 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| blues | 102 | 145 | 100 | 45 | 0 | 1 | 31 | 是 |
| classical | 95 | 103 | 100 | 0 | 0 | 1 | 6 | 是 |
| country | 106 | 163 | 100 | 61 | 0 | 1 | 50 | 是 |
| hiphop | 309 | 146 | 100 | 45 | 1 | 0 | 0 | 是 |
| jazz | 100 | 100 | 100 | 0 | 0 | 0 | 0 | 是 |
| pop | 891 | 100 | 100 | 0 | 0 | 0 | 0 | 是 |
| rock | 96 | 124 | 100 | 16 | 0 | 1（候补） | 16 | 是 |

说明：

- rock 的给定歌单仅 96 首，其中 84 首通过校验；其余 16 首来自候补歌单「欧美摇滚经典」（722234258），候补时同一歌手只收 1 首（因同歌手共跳过 7 首）；
- 已剔除 1 首无音源曲目（hiphop《Pure Water》），并向后取曲补足至 100 首；
- blues、classical、country 的给定歌单本身不足 100 首或混有民谣、新世纪等类型，需从分类歌单补足；
- 全集 700 行中含 1 组跨类重复（`Johnny B. Goode` 同时出现在 blues 与 rock），**允许跨类重复**，唯一样本 699 个。

## 已知限制

- 共 10 首歌曲的语种/类型为空，均为 `album id = 0` 的无版权/下架条目（如《七里香》《兰亭序》《发如雪》），无法定位其专辑 wiki。
- 语种与歌曲类型来自网易云「音乐百科」用户共建数据，可能缺失或存在错误（例如多语种会记为 `国语,英语`）。
- 歌单为动态歌单，歌曲数量会随歌单变化；重新运行阶段 1 即可更新。
- `data/cookies.json` 含登录凭证，已加入 `.gitignore`，请勿外传。

## 免责声明

本项目仅用于学习与技术研究，请遵守目标网站的服务条款与 robots 协议，控制请求频率，勿用于商业用途。
