# 在 Windows 上安装 Claude Code(含国内镜像)

面向 Windows 用户(尤其国内网络)的 Claude Code 安装指南。装好 Claude Code 之后,再按主 [README](../README.md) 安装 `research-to-paper` 这个 skill。

> ⚠️ **先记住一句**:**能装 ≠ 能用**。安装只是把命令行工具装到本机;真正运行时 Claude Code 要连模型 API。官方 Anthropic API(`api.anthropic.com`)和登录页(`claude.ai`)在国内通常需要**代理**才能访问。没有代理的用户请直接看下面第 4 节(改用 DeepSeek 等国内可达端点)。

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

### 情况二:无代理 —— 改用国内可达的 Anthropic 兼容端点(如 DeepSeek)
Claude Code 支持把后端指向**任意 Anthropic-API 兼容的端点**,通过环境变量设置。以 **DeepSeek** 为例(它提供 Anthropic 兼容接口):

PowerShell 里**当前会话**临时设置:
```powershell
$env:ANTHROPIC_BASE_URL  = "https://api.deepseek.com/anthropic"
$env:ANTHROPIC_AUTH_TOKEN = "你的 DeepSeek API Key"
$env:ANTHROPIC_MODEL     = "deepseek-chat"   # 或 deepseek-reasoner
claude
```

想**永久生效**(每次开终端都带上):
```powershell
setx ANTHROPIC_BASE_URL  "https://api.deepseek.com/anthropic"
setx ANTHROPIC_AUTH_TOKEN "你的 DeepSeek API Key"
setx ANTHROPIC_MODEL     "deepseek-chat"
```
设完 `setx` 要**重开终端**才生效。

> ⚠️ **请以 DeepSeek 官方文档为准**:上面的 base URL、模型名、鉴权变量名可能随 DeepSeek 更新而变化,设置前查一下它最新的"Anthropic API / Claude Code 接入"说明。其它提供国内中转的 Anthropic 兼容服务同理——把 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN` 换成它给的值即可。
>
> 用 DeepSeek 等第三方模型时:**安装本 skill、跑里面的 Python 脚本完全一样**;但"自动触发 skill、多轮对抗审稿、去 AI 判断"这些靠模型理解的环节,效果取决于该模型本身,必要时更明确地点名让它"读并执行某个 SKILL.md"。

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
