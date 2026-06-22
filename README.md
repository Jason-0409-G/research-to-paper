# research-to-paper

> [English](README.en.md) ｜ 中文

研究稿件的产出,横跨若干彼此独立、又各自容易出错的环节:确定切入角度、检索并核验文献的引用完整性、依证据强度恰当地起草、经独立审稿剔除过度声称、控制行文的可读性与可检测的 AI 痕迹,直至排版成投稿格式。这些环节通常由彼此割裂的单一用途工具或纯人工完成,而环节之间的衔接处最易出错——一处指向错误文献的 DOI、一句超出证据支持的断言、一段节奏均匀而显机械的文字,任一处都可能在评审阶段削弱整篇稿件的可信度。

**research-to-paper 将这条链整合为一套完全自包含的技能(skill)**,以单一插件的形式,将一个研究想法系统地贯穿上述全部环节,且全程将用户置于决策回路之中。其设计遵循三条原则:**严谨**——每篇文献的 DOI 经 CrossRef 逐条核验,行文措辞与证据强度严格匹配(模型与基因层面只作 predict,整体实测方可 confirm),并由多个相互独立的审稿主体对抗式复核;**自包含**——检索、核验、审稿、写作、去 AI、排版均内置于本技能,不依赖任何外部 skill,安装本插件即获完整流水线;**可审计**——每一处写作判断与每一处去 AI 改动都留有可追溯的记录矩阵,而非黑箱产出。

整条流水线为:**研究想法 → 确定方向(含目标期刊及其投稿要求)→ 建立经核验的文献库 → 起草 → 多轮对抗审稿 → 去 AI(含长短句调节)→ 输出 LaTeX / Word / PDF**;各环节亦可单独调用。

适用于 **Claude Code** 与 **Codex**。

---

## 安装

### Claude Code

**方式一 · 插件市场(推荐)**

```
/plugin marketplace add Jason-0409-G/research-to-paper
/plugin install research-to-paper@research-to-paper
/reload-plugins
```

**方式二 · 脚本(克隆后本地安装)**

```bash
git clone https://github.com/Jason-0409-G/research-to-paper.git
cd research-to-paper
bash install.sh claude          # macOS / Linux
# Windows PowerShell:  .\install.ps1 -Target claude
```
安装后**重启 Claude Code**,直接请其"按 research-to-paper 的流程执行"即可。

### Codex

```bash
git clone https://github.com/Jason-0409-G/research-to-paper.git
cd research-to-paper
bash install.sh codex           # macOS / Linux
# Windows PowerShell:  .\install.ps1 -Target codex
```
脚本会将 7 个 skill 复制至 `~/.codex/skills/`(Claude 则为 `~/.claude/skills/`)。**重启 Codex** 后即可使用;`bash install.sh all` 可一次安装两者。

---

## 更新

本仓库每次推送都自动算一个新版本(`plugin.json` 不固定版本号,改用 git commit SHA),已安装的版本这样更新到最新:

**插件市场装的**
```
/plugin marketplace update research-to-paper
/reload-plugins
```
`marketplace update` 拉取最新并更新已装插件;`/reload-plugins` 让本会话立即生效,或重启 Claude Code 亦可。

**脚本装的**
```bash
cd research-to-paper   # 之前 clone 的目录
git pull
bash install.sh all    # claude / codex / all
```
然后**重启 Claude Code / Codex**。

---

## 七个子 skill 的职能

| 子 skill | 职能 |
|---|---|
| **research-to-paper** | 主编排。识别当前所处环节,按需将请求导入 **确定方向 → 建库 → 写作 → 排版**,各环节均可独立调用。 |
| **research-to-paper-scope** | **确定方向**。先检索权威文献以厘清领域脉络,再以逐项确认的方式依次定下:切入角度 / 研究问题 → 范围 → **目标期刊** → **篇幅字数** → 核心子主题;目标期刊一经确定,即**联网查询该刊投稿要求**(收录范围、文章类型、篇幅、结构、引用格式)。产出 `scope_brief.md`。 |
| **research-to-paper-curate** | **建立文献库 + 资源检索**。五源文献检索(OpenAlex / Europe PMC / PubMed / Semantic Scholar / Crossref)→ 逐篇经 **CrossRef 核验 DOI**(可识别"能够解析但指向错误文献"的情形并找回正确 DOI)→ **多 agent 对抗审查**,剔除伪造与错误归属的条目 → **配置了 Zotero API 即按分类直接导入**,否则导出 **RIS(Zotero/EndNote 通用)+ BibTeX + 按主题着色的 Excel**。另可检索生物**资源**库:任意 NCBI Entrez 库(蛋白 / 核酸 / 基因 / 物种 / 组装 / 结构 / SRA …)+ UniProt / RCSB PDB / AlphaFold / Europe PMC。 |
| **research-to-paper-write** | **写作**。先理解内容、复述核心论点并与用户确认 → 列**逐单元 rationale 矩阵**(不套用固定 IMRaD 模板)→ 按**证据对冲**原则起草(模型 / 基因层面仅作 predict、整体实测方可 confirm);并编排后续审稿与去 AI 环节。覆盖五种场景:期刊论文 / 会议论文 / 报告 / 综述 / 竞赛。 |
| **research-to-paper-audit** | **多轮对抗审稿**。调度 **3 个相互独立的审稿 agent**(claim 支撑 / 逻辑结构 / 引用证据)与主编综合,**循环审至一轮无新问题为止**;重点检出过度声称、缺乏依据的 claim、结果区混入解读、改动流于表面、引用无法支撑其所在句等问题。可单独调用("审阅这篇草稿")。 |
| **research-to-paper-humanize** | **降低 AI 痕迹**。沿**五个维度**改写:**D1 句长(长短句结合)**、D2 段落结构变化、D3 信息密度起伏、D4 连接词控制(删除"首先 / 其次 / 此外 / 值得注意的是"等)、D5 术语表述变体;分 light / medium / heavy 三档,每处改动登记入 `humanize_matrix.md`,再以 `humanize_check.py` 作**量化校验**。可单独调用("降低这段文字的 AI 痕迹")。 |
| **research-to-paper-build** | **输出格式**。以 pandoc 将定稿渲染为 **LaTeX(.tex)/ Word(.docx)/ PDF**,并依据 `library.bib` 将 `[@key]` 引用解析为参考文献表。 |

各环节均可**单独触发**:"核验这些 DOI""降低这段文字的 AI 痕迹""审阅这份草稿""导出为 Word"等指令都会直接命中对应 skill。

---

## 文档

GitHub 顶部标签栏(README / MIT license)只认一组**固定的标准文件**,无法挂任意说明文档。这里给出全部说明的一键入口:

**参考文档**
- [生物公共接口 + API 凭据](skills/research-to-paper-curate/references/bio-sources.md)
- [工作区与产物规范](skills/research-to-paper/references/artifacts.md)
- [写作技艺:对冲阶梯 + 各场景结构](skills/research-to-paper-write/references/writing-craft.md)
- [三审 prompt + 主编综合](skills/research-to-paper-audit/references/audit-prompts.md)
- [五维去 AI 规则](skills/research-to-paper-humanize/references/humanize-rules.md)
- [文献对抗审查门](skills/research-to-paper-curate/references/adversarial-review.md)
- [API 凭据模板 `.env.example`](.env.example)

**各子 skill 说明**
- [research-to-paper(主编排)](skills/research-to-paper/SKILL.md) · [scope 定方向](skills/research-to-paper-scope/SKILL.md) · [curate 建库 / 检索](skills/research-to-paper-curate/SKILL.md) · [write 写作](skills/research-to-paper-write/SKILL.md) · [audit 对抗审稿](skills/research-to-paper-audit/SKILL.md) · [humanize 去 AI](skills/research-to-paper-humanize/SKILL.md) · [build 排版](skills/research-to-paper-build/SKILL.md)

---

## 工作模式、场景与深度

- **两种入口**:**改写已有稿**(Rewrite Existing —— 在你的草稿上提升论证 / 结构 / 对冲,不降级为表面润色)或**从素材构建**(Build From Materials —— 用笔记、数据、图、PDF、部分初稿从零起草)。
- **目标场景**:`journal` 期刊论文 · `conference` 会议论文 · `report` 报告 · `review` 综述 · `competition` 竞赛论文 / 报告(各自结构不同)。
- **研究深度**:`flash`(3 篇场景样例 + 3 篇近期同领域 + 官方要求)或 `pro`(6 + 6)。
- **输出语言**:`English` 或 `Chinese`(去 AI 检查按 `--lang` 匹配)。

这些由 `research-to-paper-scope` 一问一确认地定下,写入 `scope_brief.md`,后续各阶段照此执行。

---

## 公共数据检索接口

`research-to-paper-curate` 内置接入下列公共 API,**检索/读取一律免 key**(key 仅提速;唯 Zotero 直接写入需 key)。文献用 `search_papers.py` 五源合并去重,生物资源用 `bio_search.py`。

- **文献**:OpenAlex、Europe PMC、PubMed、Semantic Scholar、Crossref。
- **生物资源**:任意 **NCBI Entrez** 库(`protein` / `nucleotide` / `gene` / `taxonomy` / `genome` / `assembly` / `structure` / `sra` / `bioproject` / `biosample` …)、**UniProt**、**RCSB PDB**、**AlphaFold DB**、**Europe PMC**。

| 接口 | 读取要 key? | 没 key | 有 key |
|---|---|---|---|
| OpenAlex / Crossref / Europe PMC | 否 | 免费(邮箱进 polite 池更快) | — |
| NCBI Entrez(全库) | 否 | 3 次/秒 | `NCBI_API_KEY` → 10 次/秒 |
| Semantic Scholar | 否 | 共享池(可能限速) | `S2_API_KEY` 专属限额 |
| UniProt / RCSB PDB / AlphaFold | 否 | 完全免 key | — |
| **Zotero 直接导入** | **要(写入)** | 回退 `.ris` 文件 | 按分类直推进库 |

```bash
python bio_search.py protein "class IIa bacteriocin" --retmax 10
python bio_search.py uniprot "pediocin"        # → P29430 Bacteriocin pediocin PA-1
python bio_search.py pdb "bacteriocin"         # → 1O82 / 5UKZ …
python bio_search.py alphafold P29430          # 查询参数 = UniProt 登录号
python bio_search.py --list                    # 列出全部接口
```
逐接口的 key 获取方式与速率见 `skills/research-to-paper-curate/references/bio-sources.md`。

---

## 工作产物(可审计轨迹)

一次完整运行不只产出最终稿,而是在统一工作区留下可追溯的写作轨迹(`new_workspace.py` 脚手架,各阶段写入):

```
manuscript_workspace/
├── scope_brief.md              # scope:方向契约(角度 / 目标期刊及要求 / 字数 / 主题)
├── library/
│   ├── library.ris             # curate:Zotero / EndNote 通用
│   ├── library.bib             # curate:pandoc / LaTeX
│   └── library.xlsx            # curate:按主题着色(缺 openpyxl 退 .csv)
├── writing_rationale_matrix.md # write:逐单元写作理据(claim / 证据 / 对冲档 / 来源)
├── draft.md                    # write:工作草稿(含 [@key] 引用)
├── audit_report.md             # audit:三审 + 主编综合,逐轮直至无新问题
├── humanize_matrix.md          # humanize:逐处去 AI 改动(按 D1–D5 标注)
├── final/                      # build:main.tex / manuscript.docx / manuscript.pdf
└── artifact_manifest.md        # 由 artifact_check.py 生成的产物索引
```

最核心的两个推理产物是 `writing_rationale_matrix.md`(逐单元解释为什么这样写)与 `audit_report.md`(独立评审查到什么、如何解决)。若产出漂亮的 `draft.md` 却空着理据矩阵,即视为未完成。完整规范见 `skills/research-to-paper/references/artifacts.md`。

---

## 检查命令

每个检查都是纯标准库脚本(下方为仓库内路径;安装后脚本位于 `~/.claude/skills/` 或 `~/.codex/skills/` 下):

```bash
# 文献 DOI 真实且匹配(curate)
python skills/research-to-paper-curate/scripts/verify_doi.py <papers.json> <verified.json>

# 正文 [@key] / \cite 能在 library.bib 解析(write → build)
python skills/research-to-paper/scripts/cite_check.py manuscript_workspace/draft.md manuscript_workspace/library/library.bib

# 去 AI 痕迹达标(humanize;--tier light/medium/heavy)
python skills/research-to-paper-humanize/scripts/humanize_check.py manuscript_workspace/draft.md --lang zh --tier medium

# 产物轨迹完整,并刷新 manifest(orchestrator)
python skills/research-to-paper/scripts/artifact_check.py manuscript_workspace --write

# 检查脚本的单元测试
python -m unittest discover -s tests
```

---

## 依赖

除下列可选工具外,其余均为 Python **标准库**(缺失时将优雅降级或给出提示):

- **`openpyxl`**(Python)— 用于生成着色 `.xlsx`;缺失时 curate 改为输出 `.csv`,RIS / BibTeX 不受影响。
- **`pandoc`** — `research-to-paper-build` 输出 LaTeX / Word 所必需(`brew install pandoc` / `apt install pandoc` / Windows 用 winget 或 choco)。
- **TeX 引擎**(xelatex / pdflatex)— 仅 PDF 需要;缺失时仍会输出 `.tex`,可另行编译。
- **API 凭据(全部可选)** — 复制 `.env.example` 为 `.env`(或 `~/.config/research-to-paper/keys.env`)填入:`CROSSREF_MAILTO` / `NCBI_EMAIL` 进更快的 polite 池;`NCBI_API_KEY` / `S2_API_KEY` 提升限速;`ZOTERO_API_KEY` + `ZOTERO_USER_ID` 则把文献**直接按分类导入 Zotero**(EndNote 无公开写入 API,仍走 `.ris` 文件导入)。`.env` 已被 gitignore,不入仓库;无任何 key 也能用。

---

## 用法举例

直接陈述需求即可,例如:

- "我有一个研究方向但尚未定题——请先确定方向与切入点,检索权威文献、核验 DOI,再撰写为综述。"
- "核验这批参考文献的 DOI,剔除无法核实的条目,导出为可导入 EndNote 的文献库。"
- "降低这段文字的 AI 痕迹,注意长短句结合。" ／ "审阅这篇草稿是否存在过度声称。"
- "将这份稿件导出为 LaTeX 与 Word。"

主编排仅执行所需环节,并在进入下一环节前说明每一步的产出。

---

## 校验(改完插件后)

```
claude plugin validate .
```
