#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TodoTagger - 一个优雅的TODO注释追踪工具

这个工具可以扫描项目中的TODO注释，按重要性分类，
并以多种格式输出结果，帮助开发者更好地管理任务。

"""

import re
import sys
import json
import argparse
import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Set
from colorama import Fore, Style, init

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
    def console(todos: List[TodoItem]) -> str:
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
            
        lines.extend([
            "=" * 80,
            f"总计: {len(todos)} 个TODO项"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def markdown(todos: List[TodoItem], output_file: str = "todo_report.md") -> str:
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
            
            content = "".join(content)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Markdown报告已生成: {output_file}"
    
    @staticmethod
    def json(todos: List[TodoItem], output_file: str = "todo_report.json") -> str:
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
    
    # 格式化输出
    formatter = OutputFormatter()
    
    if args.output == 'console' or args.output == 'all':
        print(formatter.console(todos))
    
    if args.output == 'markdown' or args.output == 'all':
        result = formatter.markdown(todos)
        if not args.quiet:
            print(result)
    
    if args.output == 'json' or args.output == 'all':
        result = formatter.json(todos)
        if not args.quiet:
            print(result)

if __name__ == "__main__":
    main() 