# Beta24919 多子网格与颜色绑定离线校验

本轮不启动游戏，不改 guest/、combat/、native-host/、dev_cycle.sh 或 native_display_mode.py。
新增 `tools/ow_model_submeshes.py`，保留 `venom_mine_assets.parse_model` 原有实现及旧 `.mesh.json` 数据；主链改指向新的 `.lod0.mesh.json`，`legacyFile` 保留旧路径。
每个三角形有 `triangleTextureIds`；每个子网格记录原始索引范围、顶点基址、LOD 位掩码、材质槽及完整绑定/拒绝原因。

## 测得布局

输入为四个实体缓存中的原始模型，不是现代 MRNM 文件。

| 模型偏移 | 类型 | 本次验证的含义 |
|---|---|---|
| +72 | u32 | 原始文件长度 |
| +324/+326 | 2×u16 | 一致的材质槽数量；槽哈希表长度与之吻合 |
| +336/+337 | 2×u8 | 支持的单顶点/索引缓冲计数均为 1 |
| +338 | u8 | 模型 LOD mask，保留原值 |
| +339 | u8 | 子网格数量，分别为 4/14/8/1 |
| +352 | u64 | 材质槽哈希表指针，8 字节/槽 |
| +360 | u64 | 子网格表指针 |
| +368/+376 | 2×u64 | 既有顶点/索引描述指针 |

子网格表恰好占 `count*72` 字节，之后是顶点描述。每行：

| 行内偏移 | 类型 | 含义 |
|---|---|---|
| +52 | u32 | 顶点基址 VertexStart |
| +56/+58 | 2×u16 | 索引起点/索引数量，单位为 uint16 元素 |
| +60 | u16 | 实际引用的独立顶点数，**不是索引最大值加一** |
| +62 | u16 | 骨骼偏移字段（四个样本均为零，未扩展非零骨骼路径） |
| +64 | u16 | flags，样本为 46，保留原值 |
| +66/+67 | 2×u8 | 缓冲选择（本次只支持 0）、材质槽序号 |
| +68 | u8 | LOD 位掩码：1=LOD0，2/4/8=后续 LOD；255 为各 LOD 共用 |

取 `mask & 1`；逐子网格读取索引，按 `VertexStart + rawIndex` 取源顶点，再压紧映射。捕兽夹的稀疏索引最大值可大于该子网格独立顶点数：第一段有214个独立顶点，原索引最大2941；第二段1416个独立顶点、基址188、原索引最大2452。截取连续顶点或把全部 LOD 共用一个未加基址的索引数组都会出错。
解析器检查所有 LOD 的范围/独立顶点数，只导出 LOD0；不同子网格保留独立顶点映射，表内“顶点数”为导出顶点数之和，不表示整个源缓冲的唯一索引数。

已有本机源码佐证：`~/.universal-modder/toolchains/OWLib-source/TankLib/Chunks/teModelChunk_RenderMesh.cs`，其读取逻辑对稀疏索引做 remap，再加 VertexStart。仅借助该算法核验；现代128字节描述布局未被套用到24919的72字节表。既有 `tools/venom_mine_assets.py` 是顶点语义/法线/UV/刚性权重布局的来源。

## Look → 材质槽 → 颜色贴图

实体中的模型和 Look 直接引用先配对；不在全链贴图池中按尺寸/格式猜一张。
Look 的 `DUTS` 容器在 +112 为数组 count、+120 为数组 pointer；24字节行是 `ffffffffffffffff`、material GUID、slot hash。子网格槽序号查模型哈希表，再按 hash 匹配同实体 Look。
这也解释 Venom：槽1哈希 `6d6e1b6a3e6aec67` 对应 `0e00000000001b37`，槽0的 `b80e918f52992a64` 是 null 材质；不能仅按 Look 中第一次看到的 hash 绑定。
颜色候选只接受该材质引用的32字节纹理头且格式为72/78，唯一且成功解码才绑定。格式71等线性参数图明确排除；多候选、缺失、null 或冲突均输出原因，预览用中性灰。

旧链漏掉了活动材质09c4的 `0c0000000000256f`，所以原先会选粉/青参数图2570。链现在额外查活动 Look 材质中的未登记纹理引用；仅扩展默认材质表，不盲追所有皮肤变体中未打包的纹理。
捕兽夹2339材质在+176引用 `0c000000000052d7`；现有 Windows-RCN/enUS 主清单候选包逐包查找后没有找到记录，无法确认该资源的格式/内容。不能把71格式4f3b当颜色，也不能把其他实体的sRGB贴图借过来。保留 raw 材质、缺失引用及 `missingTextureResources`；这不证明其他语言/平台目录也不存在该纹理。

## 四模型结果

| 实体 / 模型 | LOD0 子网格 | 导出顶点 / 三角形 | 颜色绑定 |
|---|---|---|---|
| `0400000000000385` / `0d00000000002764` | 0 | 272 / 500 | 09c4 → `0c0000000000256f`，78 |
| `0400000000000f9b` / `0d00000000002959` | 0/1/8/10 | 1349 / 1376 | 2148 → `0c00000000004cae`，72；09c4 → `0c0000000000256f`，78 |
| `04000000000011a9` / `0d000000000028cd` | 0/4 | 1630 / 2050 | 2339 → 缺失52d7，颜色未确定，预览灰色 |
| `04000000000000af` / `0d000000000006f2` | 0（mask255） | 1079 / 1236 | 1b37 → `0c00000000001427`，78 |

只查看 `research/asset-cache/preview-junkrat.jpg` 一张768×592、quality80合图，每项两角度：红色球形榴弹、分层圆盘地雷、带齿捕兽夹和四脚Venom几何均正常，地雷/捕兽夹不再爆散。捕兽夹灰色是明确缺失颜色资源，非完整原版着色验收。预览为离线纹理采样/简化光照，不代表原版 shader 或游戏中融合验收。
原Venom `parse_model` 的 positions/normals/uv/indices、bounds/translation/height 与本轮开始前快照一致；旧 `.mesh.json` 保持不变。新LOD0网格同样保留相同数组内容。

复现：

```powershell
.venv/Scripts/python.exe tools/test_ow_model_submeshes.py
.venv/Scripts/python.exe tools/test_ow_asset_chain.py
.venv/Scripts/python.exe tools/ow_asset_chain.py 0400000000000385
.venv/Scripts/python.exe tools/ow_asset_chain.py 0400000000000f9b
.venv/Scripts/python.exe tools/ow_asset_chain.py 04000000000011a9
.venv/Scripts/python.exe tools/ow_asset_chain.py 04000000000000af --texture-layout dword
.venv/Scripts/python.exe tools/preview_asset_meshes.py research/asset-cache/preview-junkrat.jpg 0400000000000385 0400000000000f9b 04000000000011a9 04000000000000af
```

13项离线测试包括相对基址+稀疏索引、多LOD排除、共享LOD、非法范围拒绝、Look行校验、禁止全局贴图替代、线性图拒绝及缺失原因。mine链里仍有历史按偏移扫描得到的未解析09候选，trap链仍有52d7缺失；这些不被伪报为完整链，活动模型的绑定结果单独报告。
数值回执：`research/asset-cache/submesh-verification-20261025.json`。没有启动游戏或改动对照素材目录。
