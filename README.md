# AI Credits Radar

[![quality](https://github.com/mingmingma258-boop/ai-credits-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/mingmingma258-boop/ai-credits-radar/actions/workflows/ci.yml)

一个可审计的 AI API、GPU 与云 credits 机会雷达。

AI Credits Radar 把“免费层”“一次性试用额度”“需要审核的 startup credits”与“合作方/学生专属权益”分开记录，并为每条记录保留官方页面、核验日期、申请方式和风险提示。项目不代替用户创建账号、不保存 API key、不绕过验证，也不会在没有明确确认的情况下升级付费方案。

> 初始版本是在空的 GitHub 仓库基础上恢复出的可运行基线；后续历史版本可按贡献流程比对合并，仓库中已提交的文件是当前事实来源。

## 快速开始

需要 Python 3.10+，运行时无第三方依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .

credits-radar summary
credits-radar list --kind api
credits-radar list --application-only
credits-radar search gpu
credits-radar list --status conditional --sort amount
credits-radar list --access student --active-only
credits-radar validate
```

启动静态雷达页面：

```bash
python -m http.server 8080
# 浏览器打开 http://localhost:8080/web/
```

## 数据与分类

主数据在 [`data/programs.json`](data/programs.json)。每条记录包含：

- `kind`：`api`、`gpu`、`cloud`、`startup`、`trial`、`student` 或 `developer`；
- `access`：免费层、账号注册、申请审核、学生资格或合作方入口；
- `amount_usd_max` / `amount_display`：可量化额度与原始展示文本；未知或非金额权益不强行换算；
- `evidence_url`：官方证据页面；`application_url`：用户应进入的官方入口；
- `last_verified`：最后一次人工核验日期；
- `handoff`：是否通常需要登录、业务/身份验证或合作方代码；
- `payment_note` / `caution`：信用卡、自动升级、数据使用、配额和区域限制等提醒。

CLI 的 `--status` 可把“仍公开”“有条件”和“先核验”分开，`--sort amount` 使用目录中的最高展示额度排序；搜索还会覆盖申请条件、有效期和风险提示。

“active”只表示官方页面仍公开提供该机会，不代表任何人一定符合资格，也不代表额度必然获批。具体条款、地区、模型、账户历史和审核结果以供应商页面为准。

## 申请工作流

推荐顺序是：先用不需要申请审核的免费 API/GPU 资源验证 demo，再申请 startup credits；申请前准备一个事实准确的项目简介、仓库链接、预计用量和预算。不要重复注册多个账号、伪造公司/学生身份、共享邀请码或规避风控。

逐项申请时：

1. 打开 `application_url`，核对地区、资格、信用卡/账单和过期规则；
2. 只填写真实信息；需要登录、OAuth 授权、验证码、实名或最终提交时由账号持有人接管；
3. 获批后立刻设置预算/用量告警，并确认 credits 的可用服务、到期时间和是否会自动转付费；
4. 把结果记录在个人副本或 issue 中，不要把 token、账单截图或身份证件提交到仓库。

更详细的申请清单见 [`docs/application-playbook.md`](docs/application-playbook.md)。

### 中国大陆地区的额外核验

目录中的“官方页面可访问”不等于该机会一定对中国大陆账号开放。申请前应在供应商页面确认实际地区、运营主体、模型/服务可用性、付款要求和账号历史；不要用虚假地址、虚假学生身份、VPN 或重复账号规避地区与风控限制。微软全球 Azure 与“中国区 Azure（由 21Vianet 运营）”是分开的服务环境，学生邮箱能否通过验证也以页面实际结果为准。可先查看 [Azure for Students](https://azure.microsoft.com/en-us/free/students) 的学生要求与 [Azure 中国区](https://www.azure.cn/en-us/) 的服务说明。

## 项目结构

```text
data/programs.json              # 可审计机会目录
src/ai_credits_radar/           # Python CLI 与校验器
tests/                           # 标准库单元测试
web/                             # 无构建步骤的静态浏览器页面
docs/application-playbook.md    # 申请和交接边界
```

## 贡献与维护

新增记录时必须使用官方入口或官方文档作为证据，并填写 `last_verified`。如果额度随账户、地区或模型变化，请写成条件描述，不要把搜索结果中的最高额度当成保证值。提交前运行：

```bash
credits-radar validate
python -m unittest discover -s tests -v
```

项目采用 MIT License。机会目录中的各项权益仍受对应供应商的服务条款和促销条款约束。
