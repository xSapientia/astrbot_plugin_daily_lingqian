# astrbot_plugin_daily_lingqian

<div align="center">

[![Version](https://img.shields.io/badge/version-0.0.1-blue.svg)](https://github.com/xSapientia/astrbot_plugin_daily_lingqian)
[![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D3.4.0-green.svg)](https://github.com/Soulter/AstrBot)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

一个模拟每日抽取观音灵签的插件，让你的AstrBot成为慈悲的观音菩萨！

</div>

## ✨ 功能特性

### 🎲 观音100灵签系统
- **每日抽签**：基于用户ID和日期生成唯一随机种子，确保每日只能抽取一次
- **智能概率调整**：可根据今日人品值（需安装daily_fortune插件）调整上签、中签概率
- **完整灵签数据**：包含观音100签的完整签文、解释、宫位等信息
- **多版本图片支持**：支持不同版本的灵签图片显示

### 🔮 AI解签系统
- **LLM智能解签**：接入大语言模型，根据用户问题智能解读灵签含义
- **多种LLM支持**：支持AstrBot配置的供应商、自定义人格、第三方OpenAI兼容接口
- **防重复处理**：智能防止同一用户同时发起多个解签请求
- **解签记录管理**：完整记录用户的解签历史和问题

### 📊 数据统计系统
- **排行榜功能**：群内今日灵签排行、解签排行，增加互动性
- **历史记录查询**：详细的个人灵签和解签历史统计
- **多维度统计**：包括上中下签分布、解签频次等多项数据

### 🛡️ 权限与安全
- **群聊白名单**：可限制插件只在指定群聊中使用
- **管理员权限**：重置、初始化等敏感操作需要管理员权限
- **数据隔离**：用户数据完全隔离，隐私安全有保障

## 🎯 使用方法

### 🎲 灵签指令

| 指令 | 别名 | 说明 | 权限 |
|------|------|------|------|
| `/lq` | `lingqian`, `抽灵签`, `灵签` | 抽取或查询今日灵签 | 所有人 |
| `/lq @某人` | `lingqian @某人` | 查询他人的今日灵签 | 所有人 |
| `/lq help` | `lingqian help` | 显示灵签帮助信息 | 所有人 |
| `/lqrank` | `lq rank`, `lingqian rank`, `lingqianrank` | 查看群内今日灵签排行榜 | 仅群聊 |
| `/lqhistory` | `lq history`, `lq hi`, `lqhi` | 查看自己的灵签历史记录 | 所有人 |
| `/lqhistory @某人` | `lq history @某人`, `lq hi @某人` | 查看他人的灵签历史记录 | 所有人 |
| `/lqdelete --confirm` | `lq delete --confirm`, `lq del --confirm` | 删除自己除今日外的历史记录 | 所有人 |
| `/lqinitialize --confirm` | `lq initialize --confirm`, `lq init --confirm` | 初始化自己今日记录 | 管理员 |
| `/lqinitialize @某人 --confirm` | `lq initialize @某人 --confirm` | 初始化他人今日记录 | 管理员 |
| `/lqreset --confirm` | `lq reset --confirm`, `lq re --confirm` | 重置所有灵签数据 | 管理员 |

### 🔮 解签指令

| 指令 | 别名 | 说明 | 权限 |
|------|------|------|------|
| `/jq [内容]` | `jieqian [内容]`, `解签 [内容]` | 依据内容解读今日灵签 | 所有人 |
| `/jq help` | `jieqian help` | 显示解签帮助信息 | 所有人 |
| `/jqlist` | `jq list`, `jieqian list` | 查看自己今日所有解签 | 所有人 |
| `/jqlist @某人` | `jq list @某人` | 查看他人今日所有解签 | 所有人 |
| `/jqlist [序号]` | `jq list [序号]` | 查看指定序号的解签内容 | 所有人 |
| `/jqrank` | `jq rank`, `jieqian rank`, `jieqianrank` | 查看群内今日解签排行榜 | 仅群聊 |
| `/jqhistory` | `jq history`, `jq hi`, `jqhi` | 查看自己的解签历史记录 | 所有人 |
| `/jqhistory @某人` | `jq history @某人`, `jq hi @某人` | 查看他人的解签历史记录 | 所有人 |
| `/jqdelete --confirm` | `jq delete --confirm`, `jq del --confirm` | 删除自己除今日外的历史记录 | 所有人 |
| `/jqinitialize --confirm` | `jq initialize --confirm`, `jq init --confirm` | 初始化自己今日记录 | 管理员 |
| `/jqinitialize @某人 --confirm` | `jq initialize @某人 --confirm` | 初始化他人今日记录 | 管理员 |
| `/jqreset --confirm` | `jq reset --confirm`, `jq re --confirm` | 重置所有解签数据 | 管理员 |

## ⚙️ 配置说明

插件支持在AstrBot管理面板中进行可视化配置：

### 🔐 权限配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `group_whitelist` | bool | false | 是否启用群聊白名单功能 |
| `groups` | list | [] | 白名单群号列表 |

### 🔗 Daily Fortune 插件联动

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `lingqian_daily_fortune_support` | bool | false | 是否读取 astrbot_plugin_daily_fortune 插件内容 |
| `lingqian_jrrp_required` | bool | false | 是否以能读取到用户本日人品数据作为使用前置条件 |
| `lingqian_jrrptip_template` | text | 「{card}」今日还未检测人品运势 | 当不满足前置条件时的提示文本模板 |
| `lingqian_ratefix` | bool | false | 是否开启概率调整功能 |
| `lingqian_shang_rate` | string | -20, -10, -5, -1, 0, 1, 3, 5, 10 | 对应人品值调整上签抽取概率 |
| `lingqian_zhong_rate` | string | -1, -3, -5, -10, 0, 1, 5, 10, 20 | 对应人品值调整中签抽取概率 |
| `daily_fortune_tip_template` | text | 「{card}」今日还未检测人品运势 | 未抽取人品时的提示模板 |

### 🎲 灵签功能配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `drawtip_template` | text | 「{card}」今日还未抽取灵签 | 未抽取灵签时的提示模板 |
| `draw_template` | text | -----「{card}」今日灵签-----\n{lqpic} | 抽取灵签模板 |
| `query_template` | text | -----「{card}」今日灵签-----\n{lqpic} | 查询灵签模板 |
| `history_content` | text | {date} 第{qianxu}签{qianming}({jixiong})\n--- | 灵签历史内容显示模板 |
| `history_template` | text | 详见配置文件 | 个人灵签历史模板 |
| `ranks_content` | text | {card} 第{qianxu}签{qianming}({jixiong})\n--- | 灵签排行显示模板 |
| `ranks_template` | text | 详见配置文件 | 群聊当日灵签排行模板 |

### 🔮 解签功能配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `tip_template` | text | 「{card}」今日还未解签 | 未解签时的提示模板 |
| `begin_template` | text | 开始为「{card}」解签... | 开始解签提示模板 |
| `ing_template` | text | 已经在为「{card}」解签中... | 解签中提示模板 |
| `template` | text | 详见配置文件 | 解签结果显示模板 |
| `list_template` | text | 详见配置文件 | 个人当日解签列表模板 |
| `persona` | string | "" | 解签时使用的人格名称 |
| `provider_id` | string | "" | 解签时调用的LLM供应商ID |
| `api_key` | string | "" | 第三方API密钥 |
| `api_url` | string | "" | 第三方API地址 |
| `model` | string | "" | 第三方API模型名称 |
| `style_prompt` | text | 详见配置文件 | 解签时的说话风格提示词 |

### 🖼️ 其他配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `lq_pics_version` | options | 100_default | 选择图片版本 |
| `lqhi_display_count` | string | 10 | 历史展现数量 |
| `uninstall_delete_data` | bool | false | 卸载时是否删除缓存数据 |
| `uninstall_delete_config` | bool | false | 卸载时是否删除配置文件 |

## 📊 灵签系统说明

### 🎯 签序分布

观音100灵签按照吉凶程度分为三个等级：

| 等级 | 数量 | 说明 |
|------|------|------|
| 上签 | 23签 | 大吉大利，诸事顺遂 |
| 中签 | 60签 | 平常运势，稳中求进 |
| 下签 | 17签 | 需要谨慎，化解不利 |

### 🔀 概率调整机制

当启用Daily Fortune插件联动时，系统会根据用户今日人品值自动调整抽签概率：

- **高人品用户**：增加上签概率，减少下签概率
- **低人品用户**：减少上签概率，增加下签概率
- **中等人品用户**：维持正常概率分布

## 💾 数据存储

插件数据保存在以下位置：

- **灵签历史**：`data/plugin_data/astrbot_plugin_daily_lingqian/lingqian_history.json`
- **解签历史**：`data/plugin_data/astrbot_plugin_daily_lingqian/jieqian_history.json`
- **解签内容**：`data/plugin_data/astrbot_plugin_daily_lingqian/jieqian_content.json`
- **插件配置**：`data/config/astrbot_plugin_daily_lingqian_config.json`

## 🔧 高级特性

### 🎯 全局数据统计
- 无论在私聊还是群聊中抽签，每个用户的今日灵签都是全局一致的
- 排行榜会显示所有抽签过的用户，不限于当前群组

### 🛡️ 防重复机制
- 采用多重保护机制防止消息重复发送
- 解签过程中的重复请求会被自动忽略

### 📊 数据安全
- 管理员清除数据需要二次确认
- 用户只能清除自己的数据
- 插件卸载时可选择性清理相关文件

## 🐛 故障排除

### 插件无响应
1. 检查插件是否已启用
2. 确认指令格式是否正确
3. 查看AstrBot日志是否有错误信息
4. 检查群聊白名单设置

### LLM解签功能不工作
1. 确认已配置大语言模型提供商
2. 检查解签配置中的LLM设置
3. 查看日志中的LLM连接状态
4. 验证人格配置是否正确

### 数据丢失
- 数据文件保存在 `data/plugin_data` 目录下
- 更新插件不会影响数据
- 只有卸载插件或手动清除才会删除数据

### 图片不显示
1. 检查图片版本配置是否正确
2. 确认 `resource` 目录下存在对应图片
3. 验证图片文件格式和命名

## 📝 更新日志

### v0.0.1 (2024-12-26)
- ✅ 实现完整的观音100灵签系统
- ✅ 添加AI智能解签功能
- ✅ 支持Daily Fortune插件联动
- ✅ 实现群内排行榜功能
- ✅ 添加详细的历史记录统计
- ✅ 支持群聊白名单功能
- ✅ 实现多版本图片支持
- ✅ 添加完善的权限管理
- ✅ 支持自定义模板配置
- ✅ 实现防重复处理机制

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发指南

1. Fork 本仓库
2. 创建新的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👨‍💻 作者

- **xSapientia** - *Initial work* - [GitHub](https://github.com/xSapientia)

## 🙏 致谢

- 感谢 [AstrBot](https://github.com/Soulter/AstrBot) 项目提供的优秀框架
- 感谢观音菩萨的慈悲护佑
- 感谢所有提出建议和反馈的用户

---

<div align="center">

如果这个插件对你有帮助，请给个 ⭐ Star！

[报告问题](https://github.com/xSapientia/astrbot_plugin_daily_lingqian/issues) · [功能建议](https://github.com/xSapientia/astrbot_plugin_daily_lingqian/issues) · [查看更多插件](https://github.com/xSapientia)

</div>
