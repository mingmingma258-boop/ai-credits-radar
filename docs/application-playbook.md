# 申请与交接清单

这份清单把可以自动化的准备工作和必须由账号持有人完成的动作分开。项目只记录公开机会，不承诺资格或获批结果。

## 优先级

如果申请人是中国大陆的个人开发者/学生，建议先走“学生资格 → 免费层 → 新客试用”的低风险顺序：

1. **学生资格**：先核对 [Azure for Students](https://azure.microsoft.com/en-us/free/students) 是否接受本校邮箱、当前地区和账号状态。官方页面目前列出学生账号的 US$100/12 个月额度，且注册不要求信用卡；这不代表每个学校域名或中国区环境都会自动通过。
2. **免费层与共享 GPU**：再用 Gemini API、Mistral、Groq、OpenRouter、Hugging Face ZeroGPU、Colab 或 Kaggle 做最小 demo；各服务的地区、登录和配额要逐页确认。
3. **云试用**：只有在确实需要云端部署时，再核对 Google Cloud、AWS、Azure、Oracle 的新客资格和付款/账单规则。

微软全球 Azure 与 Azure operated by 21Vianet 是分开的服务环境。不要用外国地址、虚假地区、VPN 或重复账号规避地区与风控；如果页面把你带到登录、学校邮箱验证、验证码、实名或最终提交，必须由账号持有人重新检查后完成。

### 第一层：先验证产品，不需要 startup 审核

先用 Gemini Developer API、Mistral Free Mode、Groq Free Tier、OpenRouter free models、Cloudflare Workers AI、Hugging Face ZeroGPU、Colab 或 Kaggle 做小规模 demo。这样可以先产生真实的仓库、用量和产品说明，避免在申请表里描述一个尚未验证的想法。

### 第二层：小额或阶段型额度

如果确实符合资格，优先查看 Google pre-funded MVP、Azure for Startups 的即时/验证额度、Google/AWS/Azure/Oracle 的新客户试用。每一个入口都要先确认账户是否已经用过同类新客优惠。

### 第三层：startup/partner credits

Google AI startup、AWS Activate、Microsoft for Startups、DigitalOcean Hatch 和 NVIDIA Inception 可能带来更大额度，但通常需要业务/产品审核、公司资料或合作方关系。不要把页面上的最大值写成保证值。

## 申请前准备

- 一句话项目描述：AI Credits Radar 维护可审计的免费 AI API、GPU 和云 credits 目录，帮助开发者先验证原型，再合规申请资源。
- 仓库地址：`https://github.com/mingmingma258-boop/ai-credits-radar`
- 真实的产品阶段、使用场景、地区、公司/个人身份和融资状态。
- 预计用量：例如每月请求量、模型/推理类型、GPU 小时、存储与网络需求。
- 预算保护：预计使用的服务、最高月度支出、用量告警和停止资源的计划。

## 必须交给用户的步骤

下列动作不会由自动化代办：

1. 输入或选择登录方式、OAuth 授权、邮箱/短信验证码；
2. 输入密码、API key、支付信息、税务信息、公司注册信息或身份证件；
3. 任何实名/学生/公司资格声明；
4. 最终点击申请提交、接受服务条款、升级付费方案或创建可能产生费用的资源。

在交接前，助手可以做的准备包括：打开官方入口、检查公开字段、整理需要的材料、把公开信息映射到草稿字段，并指出不确定项。完成交接后，用户应重新检查页面上的资格、隐私、账单和有效期。

## 获批后

- 记录授予额度、适用服务、开始/到期时间、区域和是否可叠加；
- 立即开启预算、用量和异常告警；
- 给实验资源设置自动关停或最大生命周期；
- 不把 token、cookie、账单截图、验证码或身份文件放入 Git；
- 如果额度被拒，保留供应商的原始原因，不用多个账号重复申请或伪造资料。
