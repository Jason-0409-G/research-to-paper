---
title: "research-to-paper 安装手册（Windows）"
subtitle: "安装 Claude Code · 接入 DeepSeek（免 Claude 会员）· 安装 research-to-paper"
---

# 一、概述

本手册阐述在 Windows 平台上安装 Claude Code、接入 DeepSeek 模型(无需 Claude 会员资格或登录)并安装 research-to-paper 技能的完整流程。

环境构成如下:Claude Code 为 Anthropic 发布的命令行工具;research-to-paper 以插件形式在其内运行;模型经由 DeepSeek 提供的 Anthropic 兼容接口接入。下列命令均采用国内镜像源,以提升下载速度。

# 二、前置条件

- 操作系统:Windows 10 或 Windows 11。
- DeepSeek API 凭据:登录 DeepSeek 开放平台 <https://platform.deepseek.com/>,在「API Keys」中创建,复制以 `sk-` 起始的字符串并妥善保存,不得公开。若该地址无法打开,可先访问官网 <https://www.deepseek.com/>,自顶部「API 开放平台」进入。

# 三、安装 Claude Code

**1. 启动终端。** 经开始菜单检索 `PowerShell`,启动「Windows PowerShell」。

**2. 安装 Node.js 运行环境。** 自国内镜像 <https://npmmirror.com/mirrors/node/> 进入最新 LTS 版本目录,下载适用于 Windows 的 `.msi` 安装包,按默认选项完成安装。安装毕,执行以下命令予以确认:

```powershell
node -v
```

**3. 配置 npm 镜像源并安装 Claude Code。**

```powershell
npm config set registry https://registry.npmmirror.com
npm install -g @anthropic-ai/claude-code
```

安装完成后,关闭并重新启动 PowerShell,执行以下命令予以验证:

```powershell
claude --version
```

若正确输出版本号,即表明安装成功;若提示无法识别 `claude`,请重新启动终端后再行尝试。

# 四、接入 DeepSeek(免 Claude 会员)

设定 DeepSeek 接口地址与访问令牌后,Claude Code 不再依赖 Claude 会员资格或浏览器登录;相关配置存放于 `~/.claude/settings.json`。仓库已提供预置模板,下载并填入凭据即可,无需手动创建文件。

**1. 获取模板。** 访问 <https://github.com/Jason-0409-G/scriptorium/blob/main/templates/settings.json>,点击「Download raw file」保存至本地,并确认文件名为 `settings.json`(而非 `settings.json.txt`)。

**2. 填入凭据。** 以记事本打开该文件,将 `ANTHROPIC_AUTH_TOKEN` 对应的占位字符串替换为本人的 DeepSeek 凭据,予以保存。

**3. 放置文件。** 于文件资源管理器地址栏输入 `%USERPROFILE%\.claude` 并回车(若该目录尚不存在,先于 `C:\Users\<用户名>\` 下创建名为 `.claude` 的目录),将该 `settings.json` 移入其中。

模板内容如下,供核对:

```json
{
  "hasCompletedOnboarding": true,
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "在此粘贴你的 DeepSeek API 凭据",
    "ANTHROPIC_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-pro[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_EFFORT_LEVEL": "max"
  }
}
```

注意事项:

- 访问令牌应使用 `ANTHROPIC_AUTH_TOKEN`,而非 `ANTHROPIC_API_KEY`。
- 字段 `hasCompletedOnboarding: true` 不可省略,否则首次运行 `claude` 时仍将进入引导与登录流程。
- `env` 中的各 `ANTHROPIC_*_MODEL` 与 `CLAUDE_CODE_*` 字段对应 DeepSeek 官方推荐的完整配置(主模型及 Opus / Sonnet / Haiku 映射、子代理模型、努力级别),照表填入即可;主模型名为 `deepseek-v4-pro[1m]`(含 `[1m]` 后缀,即 100 万上下文版本,以 DeepSeek 官方文档为准)。
- 上述取值以 DeepSeek 官方「Claude Code 接入」文档为准(<https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code>),其值可能随版本变更。

# 五、安装 research-to-paper

下列两种方式,择一即可。

**方式一 · 经由插件市场。** 先执行 `claude` 进入 Claude Code,继而依次输入:

```
/plugin marketplace add https://github.com/Jason-0409-G/scriptorium.git
/plugin install research-to-paper@scriptorium
/reload-plugins
```

**方式二 · 经由脚本。** 须先安装 Git for Windows(<https://git-scm.com/downloads/win>),随后于 PowerShell 执行:

```powershell
git clone https://github.com/Jason-0409-G/scriptorium.git
cd scriptorium
.\install.ps1 -Target claude
```

安装完成后,重新启动 Claude Code。

此外,仓库提供一键脚本 `setup-windows.ps1`,可自动完成 Node.js、Claude Code 及本技能的安装与 DeepSeek 配置,其用法详见 `docs/install-claude-code-windows.md`。

# 六、启动与更新

启动:于 PowerShell 执行 `claude`,随后以中文陈述需求即可。

更新已安装的版本:

- 经插件市场安装者:于 Claude Code 内执行 `/plugin marketplace update scriptorium`,继而执行 `/reload-plugins`(或重新启动)。
- 经脚本安装者:进入克隆所得目录执行 `git pull`,再执行 `.\install.ps1 -Target claude`,随后重新启动。

# 七、常见问题

| 现象 | 处置 |
|---|---|
| 无法识别 `claude` 命令 | 重新启动 PowerShell;若仍无效,确认 Node.js 已正确安装。 |
| 对话即返回网络或超时错误 | 核查 `settings.json` 中 DeepSeek 凭据、接口地址、模型名称是否正确,并确认账户余额充足。 |
| 首次运行仍进入登录流程 | `settings.json` 缺少 `"hasCompletedOnboarding": true`。 |
| `npm install` 速度过慢 | 先执行 `npm config set registry https://registry.npmmirror.com`。 |
| 提示模型不存在 | 模型名称以 DeepSeek 官方接入文档为准,据此更新。 |

# 八、安全须知

DeepSeek API 凭据属个人私有信息,仅应写入本机 `settings.json`,不得提交至代码仓库或公开渠道。如需供他人使用,应由使用者各自申请并填入其本人凭据。

# 九、参考链接

- 项目主页:<https://github.com/Jason-0409-G/scriptorium>
- Windows 安装详解(国内镜像源与一键脚本):仓库内 `docs/install-claude-code-windows.md`
- DeepSeek 接入文档:<https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code>
