# 网易云音乐歌单爬虫项目任务说明

项目文件夹根目录地址：`D:\Desktop\program\ncmWS`

本项目旨在完成一个针对于网易云音乐的爬虫工具，该爬虫工具目的为爬取指定歌单下所有歌曲的基本信息，包括歌曲名称、时长、歌手、专辑、语种、歌曲类型。

指定歌单链接：<https://music.163.com/playlist?id=565910665>

值得一提的是，为达成本项目的最终目标，可将项目整体分为三步走：

## 阶段 1：获取歌单基本信息

通过给出的 URL 进入歌单页面，获取歌曲名称、总时长、歌手和专辑这些基本信息。

- 其中歌曲信息储存于 `class="n-songtb"` 的 div 标签中。
- `class="n-songtb"` 的标签页位于 `body/contentFrame(iframe)/#document (https://music.163.com/playlist?id=565910665)/auto-id-hN67N1vC6guvrctg(div)/m-playlist(div)/g-mn4(div)/g-mn4c(div)/g-wrap6(div)` 下。
- 而具体到每首歌的信息则储存于 `n-songtb(div)/song-list-pre-cache(div id)/j-flag(div)/m-table (div)/tbody` 的每个 `tr` 下。

你需要自行解析每个 `tr` 中的信息，提取出歌曲基本信息（包括 song id、artist id、album id）。

保存爬取到的原生数据作为过程性结果，最后提取有效数据保存为 csv：

序号、歌曲名称、song id、总时长、歌手、artist id、专辑、album id

## 阶段 2：获取歌曲类型

### 2.1 构建 wiki 界面 URL

利用阶段 1 中获取到的 song id 和 album id，构建可直达相对应的网易云 wiki 界面 URL。

wiki 界面 URL 示例如下：

以歌单内第一首歌 You Are All I Need 为例，其 song id 为 27562048，所在专辑名为 Flight Number 001，album id 为 2639006，则对应的 URL 信息有两条：

- <https://music.163.com/#/wiki/song?songId=27562048&type=1>
- <https://music.163.com/#/wiki/album?albumId=2639006>

实际上你只需要通过 album id 构建专辑的 wiki 界面 URL，即可获取该歌曲所在专辑下的所有歌曲信息，遍历专辑中的所有歌曲，根据歌曲名称找到对应歌曲，即可确认该歌曲的语种和歌曲类型。

## 阶段 3：汇总输出

从阶段 1 和阶段 2 中获取到的 csv 文件中获取歌曲信息，给出两份 csv 文件：

1. 一份包含所有歌曲的全部信息（包含阶段 1 中的基本信息、所有类别 id、语种和歌曲类型）。
2. 另一份包含所有歌曲的关键信息（仅包括歌曲名称、时长、歌手、专辑、语种和歌曲类型）。
