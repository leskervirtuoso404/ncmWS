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
│   └── data/
│       ├── testset_{genre}.csv   # 分流派数据，每类 100 首
│       ├── testset_all.csv       # 七类汇总
│       ├── testset_summary.csv   # 抓取统计
│       └── raw/                  # 接口缓存（本地生成，不入库）
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

| 流派 | 歌单 | 歌单 id |
| --- | --- | --- |
| blues | 100blues大师-布鲁斯是他们的生命 | 102463641 |
| classical | 世界级古典钢琴曲音乐珍藏 | 167900089 |
| country | 美国乡村民谣之旅 | 697173945 |
| hiphop | hiphop炸曲神曲大整合 dancer必备！ | 439484002 |
| jazz | 爵士小情歌 \| 同慵懒爵士缠绵悱恻 | 2829895462 |
| pop | 我喜欢的音乐-流行 | 18639113421 |
| rock | 我喜欢的音乐-摇滚 | 18639045526 |

### 抓取规则

1. 按给定歌单的**原始顺序**逐首扫描，用专辑音乐百科的「歌曲类型」标签校验是否包含目标流派（如 blues 必须含「蓝调」）；
2. 类型不属于该风格的曲目**跳过并继续往后取**，直到该类别收满 100 首；
3. 给定歌单扫完仍不足 100 首时，从网易云对应分类（蓝调 / 古典 / 乡村 / 说唱 / 爵士 / 流行 / 摇滚）的热门歌单依次补充，补充曲目同样逐首校验标签；
4. 跨歌单按 song id 与歌名去重（同一首歌不会在同一类别内重复出现）。

### 运行

复用主项目的登录 Cookie（`data/cookies.json`），语种/类型标签取自需要登录的音乐百科接口：

```bash
python genre_testset/src/build_testset.py                 # 默认每类 100 首
python genre_testset/src/build_testset.py --target 50     # 验证用，只取 50 首
python genre_testset/src/build_testset.py --workers 4 --delay 0.2
```

接口缓存写入 `genre_testset/data/raw/`（已加入 `.gitignore`），重跑自动复用，可断点续跑；删除缓存即可完全重抓。

### 输出文件

- `genre_testset/data/testset_{genre}.csv`：分流派数据，每类 100 行
- `genre_testset/data/testset_all.csv`：七类汇总，700 行
- `genre_testset/data/testset_summary.csv`：各类抓取统计

字段：`序号, 歌曲名称, song id, 总时长, 歌手, artist id, 专辑, album id, 语种, 歌曲类型, 歌曲类型_en, genre, 歌单位置, 数据来源`

其中 `歌曲类型_en` 为中文类型标签的英文映射（如 `流行 / 摇滚` → `pop / rock`），`歌单位置` 为曲目在来源歌单中的序号，`数据来源` 为 `given_playlist` 或 `supplement_playlist:{歌单id}`。

### 抓取统计

| 流派 | 给定歌单曲目数 | 扫描曲目数 | 命中 | 类型不符跳过 | 补充歌单 | 补充曲目 | 满额 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blues | 102 | 145 | 100 | 45 | 1 | 31 | 是 |
| classical | 95 | 103 | 100 | 0 | 1 | 6 | 是 |
| country | 106 | 163 | 100 | 61 | 1 | 50 | 是 |
| hiphop | 309 | 145 | 100 | 45 | 0 | 0 | 是 |
| jazz | 100 | 100 | 100 | 0 | 0 | 0 | 是 |
| pop | 906 | 100 | 100 | 0 | 0 | 0 | 是 |
| rock | 393 | 101 | 100 | 0 | 0 | 0 | 是 |

说明：

- blues、classical、country 的给定歌单本身不足 100 首或混有民谣、新世纪等类型，需从分类歌单补足；
- pop 与 rock 来自同一用户的自建歌单，其中有 2 首同时带「流行」「摇滚」双标签（`Home We'll Go`、`On My Own`），**允许跨类重复**，因此全集 700 行中含 2 组重复样本（698 个唯一样本）。

## 已知限制

- 共 10 首歌曲的语种/类型为空，均为 `album id = 0` 的无版权/下架条目（如《七里香》《兰亭序》《发如雪》），无法定位其专辑 wiki。
- 语种与歌曲类型来自网易云「音乐百科」用户共建数据，可能缺失或存在错误（例如多语种会记为 `国语,英语`）。
- 歌单为动态歌单，歌曲数量会随歌单变化；重新运行阶段 1 即可更新。
- `data/cookies.json` 含登录凭证，已加入 `.gitignore`，请勿外传。

## 免责声明

本项目仅用于学习与技术研究，请遵守目标网站的服务条款与 robots 协议，控制请求频率，勿用于商业用途。
