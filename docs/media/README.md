# README 演示素材

本目录仅保留适合 GitHub 展示的压缩截帧和短 GIF。素材取自既有实机宣传片，未启动游戏、未补录、未生成游戏画面。完整成片、原声和原始录像保持本地忽略。

## 来源

本地源文件：`research/promo/promo-v1.mp4`，127,122,474 字节，159.2 秒，1920×1080 / 30 fps。SHA256：

```text
29ed31b42713db2b8209d644f315793c42bce3f7a5af94123eac9e94c01da6bd
```

剪辑区间依据 `research/promo/executed-shotlist.json`；成片验收记录为 `research/promo/promo-v1-verification.json`。这些是本机复核路径，不提供指向未入库文件的失效链接。宣传片：（链接待补）。

源片记录 12 位英雄的部分技能、F6–F11 与实际暮色森林维度。它不包含后续 F5 / 生存功能和冰墙修复镜头；没有把旧片中的阻塞项目改写成演示通过。

## 公开文件

| 文件 | 成片时间 | 规格 / 说明 |
| --- | ---: | --- |
| [genji-shuriken.jpg](genji-shuriken.jpg) | 4.05 s | 1280×720；原版源氏手模、手里剑和 HUD。 |
| [widowmaker-sniper.jpg](widowmaker-sniper.jpg) | 131.60 s | 1280×720；黑百合未开镜射击，原版武器与 MC 目标。 |
| [mei-freeze.jpg](mei-freeze.jpg) | 109.40 s | 1280×720；小美喷雾演示截帧；文件名不表示这一张静帧能单独证明完整冰冻流程。 |
| [twilight-forest.jpg](twilight-forest.jpg) | 155.00 s | 1280×720；真实暮色森林维度与原版麦克雷武器。 |
| [heroes-12.gif](heroes-12.gif) | 下表 | 640×360，10 fps，84 帧，8.4 秒，6,257,005 字节；无音轨，循环播放。 |

四张 JPEG 共 452,856 字节；五个媒体文件总计 6,709,861 字节（约 6.71 MB）。不把完整视频和语音复制到这里。

## GIF 的 12 个原片区间

每段 0.7 秒，按以下顺序硬切，不含开场 / 结尾占位或未通过审查的技能：

| 英雄 | 入点（秒） | 原剪辑片段 |
| --- | ---: | --- |
| 源氏 | 2.90 | `genji-primary` |
| 麦克雷 | 19.40 | `mccree-primary` |
| 法老之鹰 | 28.50 | `pharah-primary` |
| 死神 | 40.60 | `reaper-primary` |
| 士兵：76 | 50.30 | `soldier76-primary` |
| 猎空 | 63.00 | `tracer-primary` |
| 堡垒 | 73.80 | `bastion-recon` |
| 半藏 | 86.50 | `hanzo-primary` |
| 狂鼠 | 98.60 | `junkrat-primary` |
| 小美 | 108.30 | `mei-primary` |
| 托比昂 | 119.70 | `torbjorn-turret` |
| 黑百合 | 131.00 | `widowmaker-primary` |

## 导出与核查

使用本地现有 FFmpeg `N-127564-g3c92f003c7-20261015`。截帧按上表时间，`scale=1280:720:flags=lanczos`、JPEG `-q:v 3`，移除文件级元数据。GIF 从同一输入 split / trim 12 段，分别 `setpts=PTS-STARTPTS,fps=10,scale=640:360:flags=lanczos,setsar=1`，concat 后采用 `palettegen=max_colors=192:stats_mode=diff` 与 `paletteuse=dither=sierra2_4a:diff_mode=rectangle`，无音轨。

用 Pillow 逐帧读取 GIF，核对 84 帧、总时长 8,400 ms、12 段和文件大小小于 8,000,000 字节。四张 JPEG 均重新解码检查。视觉检查只看长边不超过 1024 px、JPEG 质量 80 的对照拼图；初选图片与拼图留在被忽略的 `_preview/`，没有删除原文件。

画面中的英雄、模型和游戏界面权利归相应权利人；这些演示媒体不适用未来自有代码的 MIT 授权建议。
