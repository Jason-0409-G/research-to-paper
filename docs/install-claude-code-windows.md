# 在 Windows 上安装 Claude Code(含国内镜像)

面向 Windows 用户(尤其国内网络)的 Claude Code 安装指南。装好 Claude Code 之后,再按主 [README](../README.md) 安装 `research-to-paper` 这个 skill。

> ⚠️ **先记住一句**:**能装 ≠ 能用**。安装只是把命令行工具装到本机;真正运行时 Claude Code 要连模型 API。官方 Anthropic API(`api.anthropic.com`)和登录页(`claude.ai`)在国内通常需要**代理**才能访问。没有代理的用户请直接看下面第 4 节(改用 DeepSeek 等国内可达端点)。

---

## 0 · 一键安装(推荐先试这个)

懒人路径:用仓库里的 [`setup-windows.ps1`](../setup-windows.ps1),自动装 Node + Claude Code + 本 skill,并(可选)配好 DeepSeek 后端。

1. 打开 <https://github.com/Jason-0409-G/research-to-paper/blob/main/setup-windows.ps1>,点右上角 **Download raw file** 存到电脑(比如桌面)。
2. 用**记事本**打开它,把 `$DeepSeekApiKey = ""` 引号里换成你的 DeepSeek API Key(不想用 DeepSeek、走官方登录就留空)。
3. 在该文件所在文件夹开 **PowerShell**,运行:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1
   ```
   若提示文件被阻止,先运行 `Unblock-File .\setup-windows.ps1` 再执行上一条。
4. 装完**重开一个 PowerShell**,输入 `claude` 即可开始。

> ⚠️ 填好 key 的脚本带个人凭据——**别提交到 Git、别公开**。要给别人用就把填好的副本**私下**发给对方,或让对方填自己的 DeepSeek key。
> 脚本跑失败、或想弄懂每一步,继续看下面的手动步骤。

---

## 1. 选终端

用 **PowerShell** 或 **Windows Terminal**(推荐)。怎么区分:
- PowerShell 提示符:`PS C:\Users\你的名字>`
- CMD 提示符:`C:\Users\你的名字>`

装好后**记得关掉再重开终端**,`claude` 命令才会进 PATH。

---

## 2. 安装方式

### 方式 A · 官方原生安装(PowerShell,网络好或有代理时最省事)

```powershell
irm https://claude.ai/install.ps1 | iex
```

> 这个脚本从 `claude.ai` 下载二进制,**国内无代理时可能很慢或失败**。慢的话改用下面的方式 B。
> 报错 `irm 不是可识别的命令`,说明你在 CMD 里,不是 PowerShell。

### 方式 B · npm + 国内镜像(**国内推荐**)

这条走 npm,把源换成淘宝镜像,国内下载快很多。

**B1. 先装 Node.js**(已装可跳过,需 18+)
- 国内镜像下载安装包:<https://npmmirror.com/mirrors/node/>(选最新 LTS 的 Windows `.msi`,一路下一步)
- 验证:`node -v` 能打印版本即可。

**B2. 把 npm 源换成淘宝镜像**
```powershell
npm config set registry https://registry.npmmirror.com
```

**B3. 全局安装 Claude Code**
```powershell
npm install -g @anthropic-ai/claude-code
```

### 方式 C · winget(Windows 包管理器)

```powershell
winget install Anthropic.ClaudeCode
```
> winget 不自动更新,升级要手动 `winget upgrade Anthropic.ClaudeCode`。

---

## 3. 验证安装

```powershell
claude --version
```
能打印版本号(如 `claude 2.x.x`)就装好了。`claude` 提示找不到命令,**关掉终端重开**一次。

---

## 4. 启动与登录(国内关键)

```powershell
claude
```

首次运行会让你选账号/接入方式:

### 情况一:有代理(能访问 anthropic.com / claude.ai)
- 直接按提示在浏览器登录 Claude 订阅(Pro/Max)或填 Anthropic Console 的 API Key 即可。会话内重新登录用 `/login`。

### 情况二:不登录 Claude 会员 —— 用 DeepSeek(国内可直连,推荐)

Claude Code 支持把后端指向**任意 Anthropic-API 兼容端点**;**设了端点和 token 就不走 Claude 登录、也不需要 Claude 会员**(官方鉴权优先级里 token 排在浏览器登录之前)。最稳的做法是写进 `~/.claude/settings.json`,并顺手关掉首次运行的引导。

**最省事 · 下载现成模板**:打开 [`templates/settings.json`](../templates/settings.json) → 点「Download raw file」→ 用记事本把 `ANTHROPIC_AUTH_TOKEN` 换成你的 key → 放进 `~/.claude/`。下面是手动写法与字段说明:

用记事本新建 / 编辑 `C:\Users\你的用户名\.claude\settings.json`,填入:
```json
{
  "hasCompletedOnboarding": true,
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "在这里填你的 DeepSeek API Key",
    "ANTHROPIC_MODEL": "deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash"
  }
}
```
保存后直接运行 `claude` —— **不弹登录、直接用 DeepSeek**。

要点:
- **token 用 `ANTHROPIC_AUTH_TOKEN`**(Bearer 方案),不是 `ANTHROPIC_API_KEY`。
- **`hasCompletedOnboarding: true` 很关键**:不设的话,首次 `claude` 可能仍弹出引导/登录;设了才直达。
- `ANTHROPIC_MODEL` 是主模型,`ANTHROPIC_DEFAULT_HAIKU_MODEL` 是 Claude Code 内部用的后台小模型;两个都设,行为更可控。
- ⚠️ **base URL 和模型名以 [DeepSeek 官方 Claude Code 接入文档](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code) 为准**——模型名随版本变(本文写作时大致是 `deepseek-v4-pro` / `deepseek-v4-flash`)。其它国内中转服务同理,把 base URL + token 换成它给的即可。

> 用 DeepSeek 等第三方模型时:**装 skill、跑里面的 Python 脚本完全一样**;但"自动触发、多轮对抗审稿、去 AI 判断"这些靠模型理解的环节,效果取决于该模型本身,必要时更明确地点名"读并执行某个 SKILL.md"。

---

## 5. 装好 Claude Code 之后

按主 [README — 安装](../README.md#安装) 装 `research-to-paper`:
```
/plugin marketplace add Jason-0409-G/research-to-paper
/plugin install research-to-paper@research-to-paper
/reload-plugins
```
或克隆后 `bash install.sh all`(需要 Git for Windows 提供的 Git Bash;装 Git:<https://git-scm.com/downloads/win>)。

---

## 6. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `irm : 无法识别` | 你在 CMD,不是 PowerShell | 换 PowerShell;或用方式 B(npm) |
| `claude` 命令找不到 | 终端没重载 PATH | 关掉终端窗口重开 |
| 原生安装脚本卡住/超时 | 无代理连不上 `claude.ai` | 改用方式 B(npm + 淘宝镜像) |
| 装好了但一对话就报网络/超时错误 | 连不上模型 API | 看第 4 节:挂代理,或改用 DeepSeek 等国内端点 |
| `npm install` 很慢 | 默认走国外源 | 先执行 `npm config set registry https://registry.npmmirror.com` |

---

> 镜像与第三方端点为方便国内访问而列出;官方安装与登录以 Anthropic 文档为准,DeepSeek 接入以 DeepSeek 文档为准。
