#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TodoTagger - 一个优雅的TODO注释追踪工具

这个工具可以扫描项目中的TODO注释，按重要性分类，
并以多种格式输出结果，帮助开发者更好地管理任务。

作者: Your Name
版本: 1.0.0
许可: MIT
"""

import re
import sys
import json
import argparse
import datetime
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Set, Any, Union
from colorama import Fore, Style, init

# 检查是否可以导入AI分析器
AI_ANALYZER_AVAILABLE = False
try:
    # 先尝试导入演示分析器（无需API的测试版）
    from demo_ai_analysis import analyze_todos as ai_analyze_todos_demo
    # 创建一个包装函数，忽略第二个参数
    def ai_analyze_todos(todos, config_path=None):
        return ai_analyze_todos_demo(todos)
    AI_ANALYZER_AVAILABLE = True
    print(f"{Fore.YELLOW}注意: 使用演示AI分析器。这仅提供模拟数据，不调用真实API。{Style.RESET_ALL}")
except ImportError:
    try:
        # 尝试导入正式AI分析器
        from todo_tracker.ai_analyzer import analyze_todos as ai_analyze_todos
        AI_ANALYZER_AVAILABLE = True
    except ImportError:
        try:
            # 尝试当前目录导入
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from ai_analyzer import analyze_todos as ai_analyze_todos
            AI_ANALYZER_AVAILABLE = True
        except ImportError:
            pass

# 初始化colorama
init(autoreset=True)

# ANSI 颜色转义序列
COLORS = {
    "critical": f"{Style.BRIGHT}{Fore.RED}",     # 鲜红色 (高亮)
    "high": Fore.RED,                            # 红色
    "medium": Fore.YELLOW,                       # 黄色
    "low": Fore.CYAN,                            # 青色
    "normal": Fore.GREEN,                        # 绿色
    "reset": Style.RESET_ALL                     # 重置
}

# 配置
DEFAULT_CONFIG = {
    "file_patterns": [
        "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", 
        "*.html", "*.css", "*.scss", "*.less",
        "*.java", "*.c", "*.cpp", "*.h", "*.rs", "*.go",
        "*.rb", "*.php", "*.swift", "*.kt", "*.md"
    ],
    "exclude_dirs": [
        "**/node_modules/**", "**/venv/**", "**/.git/**", 
        "**/build/**", "**/dist/**", "**/__pycache__/**"
    ],
    "comment_patterns": {
        "py": r'#\s*TODO(?:\(([^)]*)\))?:\s*(.*)',  # 支持 TODO(user): text 格式
        "js|jsx|ts|tsx|java|c|cpp|h|rs|go|swift|kt|scss|less|php": r'//\s*TODO(?:\(([^)]*)\))?:\s*(.*)',
        "html|md": r'<!--\s*TODO(?:\(([^)]*)\))?:\s*(.*)\s*-->',
        "default": r'(?:#|//|<!--)\s*TODO(?:\(([^)]*)\))?:\s*(.*)'
    },
    "priority_patterns": {
        "critical": [r'!!!', r'\bcritical\b', r'\bCRITICAL\b'],
        "high": [r'!!', r'\bhigh\b', r'\bHIGH\b'],
        "medium": [r'!', r'\bmedium\b', r'\bMEDIUM\b'],
        "low": [r'\blow\b', r'\bLOW\b']
    },
    "ai_analysis": {
        "enabled": False,
        "context_lines": 30,
        "output_file": "todo_analysis.json"
    }
}

@dataclass
class TodoItem:
    """表示一个TODO项的数据类"""
    file_path: str
    line_number: int
    content: str
    priority: str
    assigned_to: str = ""
    context: str = ""
    creation_date: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    # AI分析结果（可选）
    ai_analysis: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """将对象转换为字典"""
        return asdict(self)

    def format_console(self) -> str:
        """格式化为控制台显示的字符串"""
        priority_color = COLORS.get(self.priority, "")
        reset = COLORS["reset"]
        
        # 基本信息
        result = f"{priority_color}{self.file_path}:{self.line_number}{reset} {self.content}"
        
        # 添加分配信息（如果有）
        if self.assigned_to:
            result += f" {Style.DIM}[分配给: {self.assigned_to}]{reset}"
            
        return result


class TodoScanner:
    """TODO注释扫描器"""
    
    def __init__(self, config: Dict = None):
        """初始化扫描器"""
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
            
        # 编译正则表达式以提高性能
        self.compiled_patterns = {}
        for ext_pattern, regex in self.config["comment_patterns"].items():
            self.compiled_patterns[ext_pattern] = re.compile(regex)
            
        self.priority_patterns = {}
        for priority, patterns in self.config["priority_patterns"].items():
            self.priority_patterns[priority] = [re.compile(p) for p in patterns]
    
    def get_pattern_for_file(self, file_path: Path) -> re.Pattern:
        """根据文件扩展名获取适当的正则表达式模式"""
        ext = file_path.suffix[1:] if file_path.suffix else ""
        
        for ext_pattern, pattern in self.compiled_patterns.items():
            if re.match(f"^({ext_pattern})$", ext):
                return pattern
                
        return self.compiled_patterns["default"]
    
    def is_excluded(self, path: Path) -> bool:
        """检查路径是否应被排除"""
        path_str = str(path)
        for exclude_pattern in self.config["exclude_dirs"]:
            if Path(path_str).match(exclude_pattern):
                return True
        return False
    
    def determine_priority(self, content: str) -> str:
        """根据内容确定优先级"""
        for priority, patterns in self.priority_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    return priority
        return "normal"  # 默认优先级
    
    def extract_assigned_to(self, assigned: Optional[str]) -> str:
        """提取分配信息"""
        return assigned.strip() if assigned else ""
    
    def scan_file(self, file_path: Path) -> List[TodoItem]:
        """扫描单个文件中的TODO注释"""
        if self.is_excluded(file_path):
            return []
            
        todos = []
        pattern = self.get_pattern_for_file(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for i, line in enumerate(lines):
                    match = pattern.search(line)
                    if match:
                        assigned_to = self.extract_assigned_to(match.group(1) if match.groups() and len(match.groups()) > 1 else None)
                        content = match.group(2) if match.groups() and len(match.groups()) > 1 else match.group(1)
                        
                        # 获取上下文（前后各一行）
                        context_lines = []
                        if i > 0:
                            context_lines.append(lines[i-1].strip())
                        context_lines.append(line.strip())
                        if i < len(lines) - 1:
                            context_lines.append(lines[i+1].strip())
                        
                        context = "\n".join(context_lines)
                        
                        # 确定优先级
                        priority = self.determine_priority(content)
                        
                        todos.append(TodoItem(
                            file_path=str(file_path),
                            line_number=i + 1,
                            content=content.strip(),
                            priority=priority,
                            assigned_to=assigned_to,
                            context=context
                        ))
        except Exception as e:
            print(f"{Fore.RED}无法读取文件 {file_path}: {e}{Style.RESET_ALL}", file=sys.stderr)
            
        return todos
    
    def scan_directory(self, directory: str = '.') -> List[TodoItem]:
        """扫描目录中所有匹配的文件"""
        todos = []
        base_path = Path(directory)
        
        # 遍历所有匹配的文件
        for pattern in self.config["file_patterns"]:
            for file_path in base_path.glob(f"**/{pattern}"):
                if not self.is_excluded(file_path):
                    todos.extend(self.scan_file(file_path))
        
        # 根据优先级排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "normal": 4}
        todos.sort(key=lambda x: (priority_order.get(x.priority, 999), x.file_path, x.line_number))
        
        return todos


class OutputFormatter:
    """输出格式化器"""
    
    @staticmethod
    def console(todos: List[TodoItem], show_ai_analysis: bool = False) -> str:
        """格式化为控制台输出"""
        if not todos:
            return "没有找到TODO注释"
            
        lines = [
            "\n找到的TODO列表（按优先级排序）：",
            "=" * 80
        ]
        
        current_priority = None
        
        for todo in todos:
            # 如果优先级变化，添加一个分隔符
            if todo.priority != current_priority:
                current_priority = todo.priority
                priority_display = {
                    "critical": "紧急",
                    "high": "高优先级",
                    "medium": "中优先级",
                    "low": "低优先级",
                    "normal": "普通"
                }.get(current_priority, current_priority)
                
                if lines[-1] != "=" * 80:
                    lines.append("-" * 80)
                lines.append(f"{COLORS.get(current_priority, '')}{priority_display}:{COLORS['reset']}")
            
            lines.append(todo.format_console())
            
            # 如果有AI分析并且需要显示
            if show_ai_analysis and todo.ai_analysis:
                analysis = todo.ai_analysis
                complexity = analysis.get("complexity", "")
                hours = analysis.get("estimated_hours", "")
                approach = analysis.get("implementation_approach", "")
                
                if complexity or hours or approach:
                    lines.append(f"  {Style.DIM}└─ 复杂度: {complexity}, 估计工时: {hours}小时")
                    lines.append(f"     实现思路: {approach[:100]}{'...' if len(approach) > 100 else ''}{Style.RESET_ALL}")
            
        lines.extend([
            "=" * 80,
            f"总计: {len(todos)} 个TODO项"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def markdown(todos: List[TodoItem], output_file: str = "todo_report.md", include_ai_analysis: bool = False) -> str:
        """生成Markdown格式的报告"""
        if not todos:
            content = "# TODO 报告\n\n*没有找到TODO注释*"
        else:
            # 生成当前时间戳
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            content = [
                f"# TODO 报告\n",
                f"*生成时间: {timestamp}*\n",
                f"## 总览\n",
                f"总计: **{len(todos)}** 个TODO项\n"
            ]
            
            # 按优先级汇总统计
            priority_counts = {}
            for todo in todos:
                priority_counts[todo.priority] = priority_counts.get(todo.priority, 0) + 1
                
            content.append("| 优先级 | 数量 |\n| --- | --- |\n")
            priority_order = ["critical", "high", "medium", "low", "normal"]
            priority_names = {
                "critical": "紧急",
                "high": "高优先级",
                "medium": "中优先级",
                "low": "低优先级",
                "normal": "普通"
            }
            
            for priority in priority_order:
                if priority in priority_counts:
                    content.append(f"| {priority_names.get(priority, priority)} | {priority_counts[priority]} |\n")
            
            content.append("\n## 详细列表\n")
            
            # 按优先级分组
            current_priority = None
            
            for todo in todos:
                if todo.priority != current_priority:
                    current_priority = todo.priority
                    priority_name = priority_names.get(current_priority, current_priority)
                    content.append(f"\n### {priority_name}\n\n")
                
                file_name = Path(todo.file_path).name
                full_path = todo.file_path
                
                todo_line = f"- **[{file_name}:{todo.line_number}]({full_path}#{todo.line_number})** - {todo.content}"
                if todo.assigned_to:
                    todo_line += f" *(分配给: {todo.assigned_to})*"
                
                content.append(todo_line + "\n")
                
                # 如果有AI分析并且需要包含AI分析
                if include_ai_analysis and todo.ai_analysis:
                    analysis = todo.ai_analysis
                    complexity = analysis.get("complexity", "")
                    hours = analysis.get("estimated_hours", "")
                    approach = analysis.get("implementation_approach", "")
                    skills = analysis.get("required_skills", [])
                    challenges = analysis.get("potential_challenges", [])
                    
                    if complexity or hours:
                        content.append(f"  - **复杂度**: {complexity}\n")
                        content.append(f"  - **估计工时**: {hours}小时\n")
                    
                    if approach:
                        content.append(f"  - **实现思路**: {approach}\n")
                    
                    if skills:
                        content.append(f"  - **所需技能**: {', '.join(skills)}\n")
                    
                    if challenges:
                        content.append(f"  - **潜在挑战**: {', '.join(challenges)}\n")
                    
                    content.append("\n")
            
            # 如果有工作计划，添加工作计划部分
            has_work_plan = any(todo.ai_analysis and todo.ai_analysis.get("work_plan") for todo in todos)
            if include_ai_analysis and has_work_plan:
                # 找到第一个含有工作计划的TODO
                work_plan = None
                for todo in todos:
                    if todo.ai_analysis and "work_plan" in todo.ai_analysis:
                        work_plan = todo.ai_analysis["work_plan"]
                        break
                
                if work_plan:
                    content.append("\n## AI 建议的工作计划\n\n")
                    
                    # 总工时
                    total_hours = work_plan.get("estimated_total_hours", 0)
                    content.append(f"**总计估计工时**: {total_hours}小时\n\n")
                    
                    # 任务顺序
                    content.append("### 建议任务顺序\n\n")
                    sequence = work_plan.get("todo_sequence", [])
                    timeline = work_plan.get("suggested_timeline", {})
                    
                    content.append("| 任务 | 内容 | 建议时间 |\n| --- | --- | --- |\n")
                    for task_id in sequence:
                        # 找到对应的TODO
                        task_todo = None
                        for todo in todos:
                            if todo.ai_analysis and todo.ai_analysis.get("todo_id") == task_id:
                                task_todo = todo
                                break
                        
                        if task_todo:
                            time_suggestion = timeline.get(task_id, "")
                            content.append(f"| {task_id} | {task_todo.content} | {time_suggestion} |\n")
                    
                    # 依赖关系
                    dependencies = work_plan.get("dependencies", {})
                    if dependencies:
                        content.append("\n### 任务依赖关系\n\n")
                        for task_id, deps in dependencies.items():
                            if deps:
                                content.append(f"- **{task_id}** 依赖于: {', '.join(deps)}\n")
                    
                    # 总结
                    summary = work_plan.get("summary", "")
                    if summary:
                        content.append(f"\n### 工作计划总结\n\n{summary}\n")
            
            content = "".join(content)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Markdown报告已生成: {output_file}"
    
    @staticmethod
    def json(todos: List[TodoItem], output_file: str = "todo_report.json", include_ai_analysis: bool = True) -> str:
        """生成JSON格式的报告"""
        # 转换为字典列表
        todo_dicts = [todo.to_dict() for todo in todos]
        
        # 添加元数据
        result = {
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "total_count": len(todos)
            },
            "todos": todo_dicts
        }
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        return f"JSON报告已生成: {output_file}"
    
    @staticmethod
    def ai_analysis(ai_result: Dict, output_file: str = "todo_analysis.json") -> str:
        """保存AI分析结果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ai_result, f, indent=2, ensure_ascii=False)
        
        return f"AI分析报告已生成: {output_file}"


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="TodoTagger - 一个优雅的TODO注释追踪工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                      # 扫描当前目录
  %(prog)s -d /path/to/project  # 扫描指定目录
  %(prog)s -o json              # 输出为JSON格式
  %(prog)s -o all               # 输出所有支持的格式
  %(prog)s --ai-analyze         # 使用AI分析TODO
""")
    
    parser.add_argument('-d', '--directory', default='.',
                        help='要扫描的目录路径 (默认: 当前目录)')
    
    parser.add_argument('-o', '--output', choices=['console', 'markdown', 'json', 'all'],
                        default='console', help='输出格式 (默认: console)')
    
    parser.add_argument('-f', '--filter', choices=['critical', 'high', 'medium', 'low', 'normal', 'all'],
                        default='all', help='按优先级过滤 (默认: all)')
    
    parser.add_argument('-e', '--exclude', nargs='+', default=[],
                        help='额外要排除的目录或文件模式')
    
    parser.add_argument('-c', '--config', 
                        help='配置文件路径')
    
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='安静模式，只输出错误信息')
    
    parser.add_argument('-v', '--version', action='version', 
                        version='%(prog)s 1.0.0',
                        help='显示版本信息并退出')
    
    # AI分析相关参数
    ai_group = parser.add_argument_group('AI分析选项')
    ai_group.add_argument('--ai-analyze', action='store_true',
                          help='使用AI分析TODO项 (需要配置API密钥)')
    
    ai_group.add_argument('--ai-show', action='store_true',
                          help='在控制台输出中显示AI分析结果')
    
    ai_group.add_argument('--ai-provider', choices=['openai', 'azure', 'qwen_local'],
                          help='AI提供商 (默认: 配置文件中的设置)')
    
    ai_group.add_argument('--ai-model',
                          help='要使用的AI模型 (默认: 配置文件中的设置)')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 创建配置
    config = DEFAULT_CONFIG.copy()
    
    # 添加额外的排除模式
    if args.exclude:
        config["exclude_dirs"].extend(args.exclude)
    
    # 从文件加载配置（如果提供）
    if args.config:
        try:
            with open(args.config, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print(f"{Fore.RED}无法加载配置文件: {e}{Style.RESET_ALL}", file=sys.stderr)
    
    # 创建扫描器
    scanner = TodoScanner(config)
    
    # 显示欢迎信息
    if not args.quiet:
        print(f"{Fore.BLUE}开始扫描TODO注释...{Style.RESET_ALL}")
    
    # 扫描目录
    todos = scanner.scan_directory(args.directory)
    
    # 根据优先级过滤
    if args.filter != 'all':
        todos = [todo for todo in todos if todo.priority == args.filter]
    
    # 检查是否启用AI分析
    ai_enabled = args.ai_analyze or (config.get("ai_analysis", {}).get("enabled", False))
    
    # 如果启用了AI分析，但模块不可用
    if ai_enabled and not AI_ANALYZER_AVAILABLE:
        print(f"{Fore.YELLOW}警告: AI分析器不可用。请确保已安装必要的依赖。{Style.RESET_ALL}", file=sys.stderr)
        ai_enabled = False
    
    # 执行AI分析
    if ai_enabled and todos:
        if not args.quiet:
            print(f"{Fore.BLUE}正在使用AI分析TODO项...{Style.RESET_ALL}")
        
        # 准备要分析的TODO列表
        todos_for_ai = []
        for i, todo in enumerate(todos):
            todos_for_ai.append({
                'content': todo.content,
                'file_path': todo.file_path,
                'line_number': todo.line_number,
                'priority': todo.priority
            })
        
        # 执行AI分析
        try:
            ai_result = ai_analyze_todos(todos_for_ai, args.config or "todo_config.json")
            
            # 将分析结果合并到TODO项中
            if ai_result and "analyses" in ai_result:
                analyses = ai_result["analyses"]
                for i, analysis in enumerate(analyses):
                    if i < len(todos):
                        # 将分析结果添加到TODO项
                        todos[i].ai_analysis = analysis
            
            # 保存AI分析结果
            ai_output_file = config.get("ai_analysis", {}).get("output_file", "todo_analysis.json")
            formatter = OutputFormatter()
            result = formatter.ai_analysis(ai_result, ai_output_file)
            if not args.quiet:
                print(result)
        except Exception as e:
            print(f"{Fore.RED}AI分析过程中出错: {e}{Style.RESET_ALL}", file=sys.stderr)
    
    # 格式化输出
    formatter = OutputFormatter()
    
    if args.output == 'console' or args.output == 'all':
        show_ai = args.ai_show and ai_enabled
        print(formatter.console(todos, show_ai))
    
    if args.output == 'markdown' or args.output == 'all':
        # 获取配置中的输出文件名
        markdown_file = config.get("output", {}).get("markdown", {}).get("file_name", "todo_report.md")
        result = formatter.markdown(todos, markdown_file, include_ai_analysis=ai_enabled)
        if not args.quiet:
            print(result)
    
    if args.output == 'json' or args.output == 'all':
        # 获取配置中的输出文件名
        json_file = config.get("output", {}).get("json", {}).get("file_name", "todo_report.json")
        result = formatter.json(todos, json_file, include_ai_analysis=ai_enabled)
        if not args.quiet:
            print(result)


if __name__ == "__main__":
    main() 