# 各流派在给定歌单中被跳过的曲目位置

构建测试集时按歌单原始顺序逐首扫描，满足以下任一条件的曲目会被跳过，并继续向后取直到该类别收满 100 首：

1. **类型不符**：「歌曲类型」标签中不含该流派标签；
2. **无音源**：播放地址接口返回空 url（歌单里仍在、详情页可访问，但无法下载）；
3. **重复跳过**：歌名 + 歌手与已收录曲目相同。

- 「歌单位置」= 该曲目在原始歌单中的序号（从 1 开始）
- 收满 100 首即停止扫描，之后的位置未扫描，不计入「跳过」
- 若给定歌单扫完仍不足 100 首，其余曲目从分类歌单补充（见 README），不属于本表范围

## blues（蓝调）— 100blues大师-布鲁斯是他们的生命

歌单共 102 首，扫描前 102 首，收录 69 首，跳过 33 首；另从分类歌单补充 31 首。

**跳过的位置**：3, 5, 12, 14–16, 18, 20, 22, 25, 28, 30, 33–35, 38–39, 50, 52, 63, 65, 69–71, 75–76, 82–83, 85–86, 92, 100, 102

| 歌单位置 | 歌曲名称 | 歌手 | 实际歌曲类型 | 跳过原因 |
| --- | --- | --- | --- | --- |
| 3 | I Got The Same Old Blues | J.J. Cale | 摇滚 | 类型不符 |
| 5 | Along for the Ride | John Mayall / Billy Preston | 摇滚 | 类型不符 |
| 12 | Whipping Post | The Allman Brothers Band | 摇滚 | 类型不符 |
| 14 | That Road (Unplugged) | Larry Carlton / Robben Ford | 爵士 | 类型不符 |
| 15 | Over Under Sideways Down (Mono) | The Yardbirds | 摇滚 | 类型不符 |
| 16 | Hit The Road Jack | Ray Charles | R&B | 类型不符 |
| 18 | Corazon Espinado | Maná / Santana | 摇滚 / 拉丁音乐 | 类型不符 |
| 20 | Honky Tonk Women | The Rolling Stones | 摇滚 | 类型不符 |
| 22 | It's My Way | Buffy Sainte-Marie | 民谣 | 类型不符 |
| 25 | Hey Joe | Jimi Hendrix | R&B | 类型不符 |
| 28 | Time Has Come Today | The Chambers Brothers | 原声带 | 类型不符 |
| 30 | Get Behind the Mule | John Hammond | 流行 | 类型不符 |
| 33 | Sunshine Of Your Love | Cream | 流行 / 摇滚 | 类型不符 |
| 34 | All Right Now | Free | 流行 / 摇滚 / 原声带 | 类型不符 |
| 35 | A Lover's Question | Clyde McPhatter | R&B | 类型不符 |
| 38 | I'd Love To Change The World | Ten Years After | 摇滚 | 类型不符 |
| 39 | I Wanna Put A Tiger In Your Tank | Cyril Davies / Alexis Korner's Blues Incorporated | 流行 / 原声带 | 类型不符 |
| 50 | Pallet On the Floor | Bob Dylan / Brownie McGhee | 民谣 | 类型不符 |
| 52 | Death Don't Have No Mercy | Bob Dylan / Rev. Gary Davis | 民谣 | 类型不符 |
| 63 | Off The Wall | Walter Jacobs | 流行 / 摇滚 | 类型不符 |
| 65 | Smokestack Lightnin' | Howlin' Wolf | 摇滚 | 类型不符 |
| 69 | Let 'Em Jump Solo | Pete Johnson | 爵士 | 类型不符 |
| 70 | Twos And Fews | Meade Lux Lewis / Albert Ammons | 爵士 | 类型不符 |
| 71 | Boogie Woogie Blues | Albert Ammons | 爵士 | 类型不符 |
| 75 | Better Off with the Blues | Clarence 'Gatemouth' Brown | 爵士 | 类型不符 |
| 76 | Booty Ooty | Johnny Guitar Watson | 放克 | 类型不符 |
| 82 | Rooster Blues | Lightnin' Slim | R&B | 类型不符 |
| 83 | Everybody's Got to Cry Sometime | Earl King | R&B | 类型不符 |
| 85 | Right Place Wrong Time | Dr. John | R&B | 类型不符 |
| 86 | Suicide Solution | James Booker | 摇滚 | 类型不符 |
| 92 | St. James Infirmary | Bobby "Blue" Bland | 世界音乐 | 类型不符 |
| 100 | Call Me Baby | Charlie Patton's War | 流行 | 类型不符 |
| 102 | Eighth of January | Sid Hemphill | 乡村 | 类型不符 |

## classical（古典）— 世界级古典钢琴曲音乐珍藏

歌单共 95 首，扫描前 95 首，收录 94 首，跳过 1 首；另从分类歌单补充 6 首。

**跳过的位置**：45

| 歌单位置 | 歌曲名称 | 歌手 | 实际歌曲类型 | 跳过原因 |
| --- | --- | --- | --- | --- |
| 45 | Rhapsodie Sur Un Thème De Paganini Pour Piano & Orchestre, Op.43 : Variation XVIII : Andante Cantabile (Remasterisé En 2009) | Jean-Philippe Collard | — | 无类型信息（音乐百科缺失） |

## country（乡村）— 美国乡村民谣之旅

歌单共 106 首，扫描前 106 首，收录 50 首，跳过 56 首；另从分类歌单补充 50 首。

**跳过的位置**：3–6, 8–10, 12–17, 19, 21–22, 24–26, 28–29, 31–32, 38, 40, 43, 52, 61, 63–68, 70–73, 76–89, 91–94

| 歌单位置 | 歌曲名称 | 歌手 | 实际歌曲类型 | 跳过原因 |
| --- | --- | --- | --- | --- |
| 3 | Rhythm Of The Rain | Jason Donovan | 流行 | 类型不符 |
| 4 | Vincent | Don McLean | 民谣 | 类型不符 |
| 5 | Scarborough Fair | Hayley Westenra | 新世纪 | 类型不符 |
| 6 | 多娜多娜 | 群星 | 民谣 | 类型不符 |
| 8 | San Francisco (Be Sure To Wear Flowers In Your Hair) | Scott McKenzie | 流行 | 类型不符 |
| 9 | Massachusetts | Bee Gees | 摇滚 | 类型不符 |
| 10 | House Of The Rising Sun | The Animals | 摇滚 | 类型不符 |
| 12 | California Dreamin' | The Mamas & the Papas / The Mamas | 流行 | 类型不符 |
| 13 | Sutter's Mill | Dan Fogelberg | 流行 | 类型不符 |
| 14 | The Sound of Silence | Garfunkel / SiMoN | 原声带 | 类型不符 |
| 15 | Sealed With A Kiss | Brian Hyland | 流行 | 类型不符 |
| 16 | It Never Rains In Southern California | Albert Hammond | 流行 | 类型不符 |
| 17 | Puff The Magic Dragon | Peter, Paul & Mary | 民谣 | 类型不符 |
| 19 | 以吻封缄 | 群星 | 流行 | 类型不符 |
| 21 | Tie A Yellow Ribbon Round The Old Oak Tree | Dawn | 民谣 | 类型不符 |
| 22 | The Sound of Silence | Paul Simon | 流行 / 摇滚 | 类型不符 |
| 24 | San Francisco | Stu Larsen | 民谣 / 摇滚 / 唱作人 | 类型不符 |
| 25 | Katmandu | Bob Seger | 蓝调 | 类型不符 |
| 26 | The Weight (2000 - Remaster) | The Band | 摇滚 | 类型不符 |
| 28 | Cotton Fields | Creedence Clearwater Revival | 摇滚 | 类型不符 |
| 29 | Bad Moon Rising | Creedence Clearwater Revival | 摇滚 | 类型不符 |
| 31 | It Came Out Of The Sky | Creedence Clearwater Revival | 摇滚 | 类型不符 |
| 32 | Lodi | Creedence Clearwater Revival | 摇滚 | 类型不符 |
| 38 | Mr. Tambourine Man | Bob Dylan | 民谣 / 摇滚 / 唱作人 | 类型不符 |
| 40 | Older Chests | Damien Rice | 民谣 / 唱作人 | 类型不符 |
| 43 | Tempest | Bob Dylan | 摇滚 | 类型不符 |
| 52 | Born In Time (Outtake from 'Oh Mercy' sessions) | Bob Dylan | 民谣 | 类型不符 |
| 61 | Rhythm of the Rain | Jason Donovan | 流行 / 电子 | 类型不符 |
| 63 | Cotton Fields | Creedence Clearwater Revival | 摇滚 | 类型不符 |
| 64 | Jamaica Farewell | Harry Belafonte | 民谣 | 类型不符 |
| 65 | Moon River | Andy Williams | 爵士 | 类型不符 |
| 66 | Donna Donna | Joan Baez | 民谣 | 类型不符 |
| 67 | The Last Waltz | Engelbert Humperdinck | 流行 | 类型不符 |
| 68 | Journey Through the Past | Neil Young | 原声带 | 类型不符 |
| 70 | Top Of The World | Carpenters | 民谣 | 类型不符 |
| 71 | Stand by Me | Ben E. King | 原声带 / R&B | 类型不符 |
| 72 | Oh, Susanna! | Various Artists | 儿童 | 类型不符 |
| 73 | I'm Gonna Getcha Good! (Red Version) | Shania Twain | 流行 | 类型不符 |
| 76 | El Condor Pasa (If I Could) | Simon & Garfunkel | 流行 / 原声带 | 类型不符 |
| 77 | Raindrops Keep Falling On My Head | B.J. Thomas | 摇滚 / 原声带 | 类型不符 |
| 78 | Better Man | Robbie Williams | 流行 | 类型不符 |
| 79 | Moon River | Janet Seidel | 爵士 | 类型不符 |
| 80 | Yesterday Once More | Carpenters | 摇滚 | 类型不符 |
| 81 | Right Here Waiting | Richard Marx | 流行 | 类型不符 |
| 82 | I Swear | All-4-One | 流行 | 类型不符 |
| 83 | Jambalaya | Carpenters | 流行 | 类型不符 |
| 84 | Hotel California (2013 Remaster) | Eagles | 摇滚 | 类型不符 |
| 85 | I'd Love You To Want Me | Lobo | 流行 | 类型不符 |
| 86 | Everything I Do I Do It for You | Bryan Adams | 流行 | 类型不符 |
| 87 | House of the Rising Sun | The Animals | 摇滚 | 类型不符 |
| 88 | Changing Partners | Patti Page | 爵士 | 类型不符 |
| 89 | I Will Follow Him | Peggy March | 流行 | 类型不符 |
| 91 | Sad Movies | Boney M. | 电子 | 类型不符 |
| 92 | Sad Movies (Make Me Cry) | Sue Thompson | 流行 | 类型不符 |
| 93 | Tonight I Celebrate My Love for You | Katie Price | 流行 | 类型不符 |
| 94 | One Way Ticket | ONE OK ROCK | 摇滚 | 类型不符 |

## hiphop（嘻哈说唱）— hiphop炸曲神曲大整合 dancer必备！

歌单共 309 首，扫描前 146 首，收录 100 首，跳过 46 首；未使用补充歌单。

**跳过的位置**：16, 20, 24, 35–36, 38, 43–44, 47–49, 51, 59, 61, 65, 68, 70–73, 77, 84, 87, 91, 97–98, 101–103, 105, 107, 109–110, 112, 116, 118–119, 123–124, 130, 135, 138–139, 141, 143–144

| 歌单位置 | 歌曲名称 | 歌手 | 实际歌曲类型 | 跳过原因 |
| --- | --- | --- | --- | --- |
| 16 | это ли счастье? | Rauf & Faik | 流行 | 类型不符 |
| 20 | Figure 8 | Maliibu N Helene | 流行 | 类型不符 |
| 24 | Serenade | 舵Diverseddie | R&B | 类型不符 |
| 35 | Alive | Blue | R&B | 类型不符 |
| 36 | luv rain | Wntr | 另类/独立 | 类型不符 |
| 38 | Told You So | Freestylers | 摇滚 / 电子 | 类型不符 |
| 43 | B**ch Better Have My Money (Karetus Remix) | karetus / Rihanna | 流行 / 电子 | 类型不符 |
| 44 | Sadda Dil Vi Tu (Ga Ga Ga Ganpati) | Sachin-Jigar / Hard Kaur | 原声带 | 类型不符 |
| 47 | Toxic (Y2K & Alexander Lewis Remix) | Britney Spears / Y2K / Alexander Lewis | 流行 / 摇滚 / 电子 | 类型不符 |
| 48 | Don't Be Judging | TroyBoi | 电子 | 类型不符 |
| 49 | Chaotic | Britney Spears | 流行 | 类型不符 |
| 51 | Amsterjam with June Marieezy | FKJ | R&B | 类型不符 |
| 59 | Closer | The Chainsmokers / Halsey | 流行 | 类型不符 |
| 61 | Midnight In Paris (BRLLNT Remix) | SOMA | 流行 / 电子 | 类型不符 |
| 65 | You're the only one for me | Quinho | 流行 / 爵士 | 类型不符 |
| 68 | Finesse (Remix) | Bruno Mars / Cardi B | 放克 | 类型不符 |
| 70 | Sucker for You | Matt Terry | 流行 | 类型不符 |
| 71 | Pure Water | Mustard / Migos | 嘻哈说唱 | 无音源（播放地址为空，无法下载） |
| 72 | Forest Fires (Massappeals Remix) | Fred V & Grafix / Etherwood | 电子 | 类型不符 |
| 73 | Blazin (Original) | Spenda C | 电子 | 类型不符 |
| 77 | Rachet | K Theory | 电子 | 类型不符 |
| 84 | Propositions | The Bar-Kays | 流行 / 放克 | 类型不符 |
| 87 | Gone (Album Version) | *NSYNC | R&B | 类型不符 |
| 91 | 100 Ways | 王嘉尔 | 流行 | 类型不符 |
| 97 | Swish | OXP / Onra / Pomrad / Devin Morrison | 蓝调 | 类型不符 |
| 98 | Love Affair | UMI | R&B | 类型不符 |
| 101 | Ice Cream (Instrumental) | Raekwon | 其他 | 类型不符 |
| 102 | So in Love | Jill Scott / Anthony Hamilton | R&B | 类型不符 |
| 103 | Gonna Have A Party (Radio Mix) | Shades of Brown | 电子 | 类型不符 |
| 105 | I'm Fly | Donae'o / Sway | 流行 | 类型不符 |
| 107 | Groovin' | Jeff Bernat | R&B | 类型不符 |
| 109 | Twerk 4 Gold (Original Mix) | Valentino Khan | 电子 | 类型不符 |
| 110 | Believer | Imagine Dragons / Lil Wayne | 摇滚 | 类型不符 |
| 112 | 中原 | Rux | 电子 | 类型不符 |
| 116 | Arena | Fabian Mazur / Snavs | 电子 | 类型不符 |
| 118 | Grind | Jordan Comolli | 电子 | 类型不符 |
| 119 | Dear Neighbor (Pham Remix) | Flapo / Jenni Potts | 电子 | 类型不符 |
| 123 | Young Boss 2.0 | Lambert凌杰 / 十七草 | 流行 | 类型不符 |
| 124 | Acid Dreams | MAX / Felly | 流行 | 类型不符 |
| 130 | Remember | KATIE / Ty Dolla $ign | 流行 / R&B | 类型不符 |
| 135 | Until Morning - A COLORS SHOW | James Vickery | R&B | 类型不符 |
| 138 | TUDO BOM | Static & Ben El / J. Balvin | 流行 | 类型不符 |
| 139 | If (Brothers In Rhythm House Mix) | Janet Jackson / Brothers In Rhythm | R&B | 类型不符 |
| 141 | Sneaky | Lil Fizz / Jhené Aiko | R&B | 类型不符 |
| 143 | Twinz (Deep Cover 98) | Big Pun / Fat Joe | 其他 | 类型不符 |
| 144 | Not Today | Mary J. Blige | 流行 | 类型不符 |

## jazz（爵士）— 爵士小情歌 | 同慵懒爵士缠绵悱恻

歌单共 100 首，扫描前 100 首，收录 100 首，跳过 0 首；未使用补充歌单。

**跳过的位置**：—

| 歌单位置 | 歌曲名称 | 歌手 | 实际歌曲类型 | 跳过原因 |
| --- | --- | --- | --- | --- |

## pop（流行）— 我喜欢的音乐-流行

歌单共 906 首，扫描前 102 首，收录 100 首，跳过 2 首；未使用补充歌单。

**跳过的位置**：34, 62

| 歌单位置 | 歌曲名称 | 歌手 | 实际歌曲类型 | 跳过原因 |
| --- | --- | --- | --- | --- |
| 34 | Always with me(口琴版) | V.A. | 流行 | 无音源（播放地址为空，无法下载） |
| 62 | 《夜色钢琴曲》虹之间 | 赵海洋 | 流行 | 无音源（播放地址为空，无法下载） |

## rock（摇滚）— 我喜欢的音乐-摇滚

歌单共 393 首，扫描前 102 首，收录 100 首，跳过 2 首；未使用补充歌单。

**跳过的位置**：73, 90

| 歌单位置 | 歌曲名称 | 歌手 | 实际歌曲类型 | 跳过原因 |
| --- | --- | --- | --- | --- |
| 73 | The Fear | The Score | 摇滚 | 无音源（播放地址为空，无法下载） |
| 90 | Numb | Linkin Park | 摇滚 / 金属 | 重复跳过（与第 13 首同名同歌手） |
