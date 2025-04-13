# TodoTagger 📝✨

<div align="center">

![版本](https://img.shields.io/badge/版本-1.0.0-blue.svg)
![许可证](https://img.shields.io/badge/许可证-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.6+-yellow.svg)

</div>

一个优雅而实用的工具，帮助开发者追踪和管理代码中的TODO注释。TodoTagger能够智能分析代码中的TODO标记，按优先级分类，并生成美观的报告。更支持使用AI分析工作量并生成工作计划。

## ✨ 特色功能

- 🔍 **智能扫描**：自动检测多种编程语言中的TODO注释
- 🎯 **优先级识别**：根据注释内容自动判断任务的优先级
- 👤 **任务分配**：支持`TODO(用户名):`格式来标记任务归属
- 🌈 **彩色输出**：在终端中以醒目的颜色直观显示不同优先级的TODO项
- 📊 **多种报告格式**：支持控制台、Markdown和JSON格式输出
- ⚙️ **高度可配置**：通过配置文件自定义各种行为
- 🧠 **AI分析**：使用AI分析任务复杂度、工作量，并生成合理的工作计划

## 📸 效果展示

<div align="center">
<img src="https://via.placeholder.com/800x400?text=TodoTagger+Console+Output" alt="TodoTagger控制台输出" width="80%"/>
</div>

## 🚀 快速开始

### 安装依赖

```bash
pip install colorama requests
```

### 基本使用

```bash
# 扫描当前目录
python todo_tagger.py

# 扫描指定目录
python todo_tagger.py -d /path/to/your/project

# 使用Markdown输出
python todo_tagger.py -o markdown

# 只显示高优先级TODO
python todo_tagger.py -f high

# 使用AI分析功能
python todo_tagger.py --ai-analyze --ai-show
```

## 📝 TODO格式支持

TodoTagger支持以下TODO注释格式：

```python
# TODO: 这是一个普通优先级任务
# TODO: 这是一个高优先级任务!!!
# TODO(张三): 这个任务分配给张三
```

```javascript
// TODO: 普通任务
// TODO: 高优先级任务!!!
// TODO(lisi): 这个任务分配给李四
```

```html
<!-- TODO: HTML中的TODO任务 -->
```

## 🌟 优先级判断

TodoTagger根据注释内容智能判断优先级：

| 优先级 | 标记方式 | 显示颜色 |
|--------|---------|---------|
| 紧急   | `TODO: 内容!!!!` 或 包含"紧急"/"立刻"等词语 | <span style="color:red;font-weight:bold">鲜红色(高亮)</span> |
| 高     | `TODO: 内容!!!` 或 包含"高"/"high"等词语 | <span style="color:red">红色</span> |
| 中     | `TODO: 内容!!` 或 包含"中"/"medium"等词语 | <span style="color:yellow">黄色</span> |
| 低     | `TODO: 内容!` 或 包含"低"/"low"等词语 | <span style="color:cyan">青色</span> |
| 普通   | `TODO: 内容`（无特殊标记） | <span style="color:green">绿色</span> |

## 🧠 AI分析功能

TodoTagger提供强大的AI分析能力，可以：

- 分析每个TODO任务的复杂度
- 估算所需工作时间
- 提供实现思路和建议
- 识别潜在挑战和所需技能
- 生成合理的工作计划和时间线

### 配置AI功能

在`todo_config.json`中配置AI功能：

```json
{
  "ai_config": {
    "provider": "openai",
    "api_key": "your_api_key",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo"
  },
  "ai_analysis": {
    "enabled": true,
    "context_lines": 30,
    "output_file": "todo_analysis.json"
  }
}
```

支持多种AI提供商：
- `openai` - OpenAI API
- `azure` - Azure OpenAI服务
- `qwen_local` - 本地部署的通义千问等模型

### 使用AI分析

```bash
# 启用AI分析并在控制台显示分析结果
python todo_tagger.py --ai-analyze --ai-show

# 指定AI提供商和模型
python todo_tagger.py --ai-analyze --ai-provider openai --ai-model gpt-4

# 生成带AI分析的Markdown报告
python todo_tagger.py -o markdown --ai-analyze
```

### 演示模式

项目内置了演示分析器，无需配置API密钥即可体验AI功能：

```bash
# 使用演示模式
python todo_tagger.py --ai-analyze --ai-show

# 或单独运行演示分析器
python demo_ai_analysis.py
```

### 示例AI分析输出

```
紧急:
app/api/auth.py:45 用户登录失败时没有提供详细错误信息
  └─ 复杂度: 中等, 估计工时: 2.5小时
     实现思路: 使用Flask的错误处理机制，实现更详细的错误报告，确保安全性
```

### 工作计划

AI还将生成完整的工作计划，包括：

- 建议的任务处理顺序
- 总工作量估计
- 每个任务的时间安排
- 任务之间的依赖关系
- 工作计划总结

## ⚙️ 配置选项

TodoTagger支持通过JSON配置文件自定义行为：

```bash
python todo_tagger.py -c todo_config.json
```

配置文件示例：
```json
{
  "file_patterns": ["*.py", "*.js"],
  "exclude_dirs": ["**/node_modules/**"],
  "priority_patterns": {
    "critical": ["!!!!", "紧急", "立刻"]
  },
  "ai_config": {
    "provider": "openai",
    "api_key": "your_api_key"
  }
}
```

## 📋 命令行参数

```
usage: todo_tagger.py [-h] [-d DIRECTORY] [-o {console,markdown,json,all}]
                      [-f {critical,high,medium,low,normal,all}]
                      [-e EXCLUDE [EXCLUDE ...]] [-c CONFIG] [-q] [-v]
                      [--ai-analyze] [--ai-show]
                      [--ai-provider {openai,azure,qwen_local}]
                      [--ai-model AI_MODEL]

选项:
  -h, --help            显示帮助信息并退出
  -d, --directory DIRECTORY
                        要扫描的目录路径 (默认: 当前目录)
  -o, --output {console,markdown,json,all}
                        输出格式 (默认: console)
  -f, --filter {critical,high,medium,low,normal,all}
                        按优先级过滤 (默认: all)
  -e, --exclude EXCLUDE [EXCLUDE ...]
                        额外要排除的目录或文件模式
  -c, --config CONFIG   配置文件路径
  -q, --quiet           安静模式，只输出错误信息
  -v, --version         显示版本信息并退出

AI分析选项:
  --ai-analyze          使用AI分析TODO项 (需要配置API密钥)
  --ai-show             在控制台输出中显示AI分析结果
  --ai-provider {openai,azure,qwen_local}
                        AI提供商 (默认: 配置文件中的设置)
  --ai-model AI_MODEL   要使用的AI模型 (默认: 配置文件中的设置)
```

## 🛠️ 进阶用法

### 生成所有格式的报告

```bash
python todo_tagger.py -o all
```

### 排除特定目录

```bash
python todo_tagger.py -e "**/test/**" "**/docs/**"
```

### 在CI/CD管道中使用

```bash
python todo_tagger.py -q -o json -f critical,high
```

## 🤝 贡献

欢迎贡献、问题和功能请求！随时提交PR或创建Issue。

## 📜 许可证

本项目基于MIT许可证开源。 