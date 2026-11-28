# 音频下载说明（country / hiphop）

按 `genre_testset/data/testset_country.csv` 与 `testset_hiphop.csv` 中列出的歌曲，逐首下载音频文件，保存到 `genre_testset/dataset/<流派>/` 下。

## 目录与命名

```
genre_testset/
├── data/
│   ├── testset_country.csv      # 歌曲清单（song id 来源）
│   └── testset_hiphop.csv
├── dataset/
│   ├── country/                 # 100 个音频文件
│   └── hiphop/                  # 100 个音频文件
└── src/
    └── download_audio.py        # 本脚本
```

命名规则与 `dataset` 下原有 mp3 一致：`歌手 - 歌曲名称.扩展名`

- 多歌手用 ` & ` 连接，如 `Johnny Cash & Willie Nelson & Waylon Jennings & Kris Kristofferson - Highwayman.m4a`
- 文件名非法字符 `\ / : * ? " < > |` 会被替换为 `_`，如 `Wynners - 4_55(part of game).m4a`
- 扩展名取自实际下载直链，绝大多数为 `.m4a`，个别歌曲仅能取到 mp3 时保存为 `.mp3`

## 实现方式

复用 `src/step4_audio.py` 中已验证的抓取逻辑（`build_filename` / `fetch_play_url` / `download`），流程：

1. 读取两个流派的 CSV，取 `song id`；
2. 调用 `/api/song/detail` 批量（每批 200）获取权威歌名与歌手，用于命名；
3. 逐首请求播放直链接口（需登录 Cookie `data/cookies.json`）：

   ```
   GET https://music.163.com/api/song/enhance/player/url/v1?ids=[{song_id}]&level=exhigh&encodeType=aac
   ```

   即网页端点击播放时实际发出的请求；若返回 `url` 为空，回退旧接口 `?ids=[...]&br=320000`；
4. 直链为空则视为无音源（无版权/下架/需付费），计入失败并跳过；
5. 带 Cookie 流式下载到 `.part` 临时文件，校验大小（< 100 KB 视为无效）后重命名为正式文件名；
6. 目标文件已存在时跳过（`--overwrite` 可覆盖），便于断点续跑。

并发：默认 4 线程（每线程独立会话），每首播放地址请求后间隔 0.2 s。

## 用法

```bash
# 默认下载 country + hiphop 全部歌曲
python genre_testset/src/download_audio.py

# 只处理某一流派
python genre_testset/src/download_audio.py --genres country

# 先试前 2 首
python genre_testset/src/download_audio.py --genres country --limit 2

# 覆盖已存在文件 / 调整并发
python genre_testset/src/download_audio.py --overwrite --workers 2
```

| 参数 | 说明 |
| --- | --- |
| `--genres` | 流派列表，默认 `country hiphop`，对应 `data/testset_<genre>.csv` |
| `--limit` | 每个流派只处理前 N 首（验证用） |
| `--workers` | 下载并发数，默认 4 |
| `--delay` | 每首播放地址请求后的间隔秒数，默认 0.2 |
| `--overwrite` | 覆盖已存在的同名文件 |

运行结束会输出各流派的成功 / 跳过 / 失败数量与新增体积，并列出失败歌曲及原因；存在失败时退出码为 1。

## 本次执行结果

| 流派 | 文件数 | 总体积 | .m4a | .mp3 | 失败 |
| --- | --- | --- | --- | --- | --- |
| country | 100 | 659.6 MB | 100 | 0 | 0 |
| hiphop | 100 | 710.3 MB | 96 | 4 | 0 |
| 合计 | 200 | 1370 MB | 196 | 4 | 0 |

无音源的歌曲在构建测试集阶段已被剔除，因此本次全部 200 首均成功取得音频；country 中有 2 首在试跑时已下载，正式运行时按「同名文件已存在」跳过。

仅能取到 mp3（exhigh/aac 无直链，回退旧接口）的 4 首：

- `Amerigo Gazaway & Mobb Deep - Mobb Brown - The G.O.D. Father of Soul Pt. III (Soul Mates Remix).mp3`
- `Big Daddy Kane - Any Type of Way.mp3`
- `Lacrim - Corleone.mp3`
- `SWV & Wu-Tang Clan - Anything (Old Skool Radio Version).mp3`

## 校验

- `dataset/country`、`dataset/hiphop` 各 100 个文件，无重名、无小于 100 KB 的异常文件；
- 抽样检查文件头为 `ftyp / M4A `，可正常播放。

## 注意事项

- 音频文件体积较大（约 1.37 GB），`dataset/` 未纳入 git 版本管理，仅供本地流派识别实验使用；
- 下载直链带时效签名（`authSecret`、`vuutv`），过期后需重新请求接口，脚本每次运行都会重新获取；
- 若歌单后续变动导致 CSV 与线上不一致，以 CSV 中的 song id 为准重新运行即可（已存在文件自动跳过）。
