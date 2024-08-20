#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from pathlib import Path
from colorama import Fore, init

# 初始化colorama
init()

def get_priority(todo_text):
    """根据TODO注释的内容判断优先级"""
    if '!!!' in todo_text:
        return 0, Fore.RED  # 高优先级，红色
    elif '!!' in todo_text:
        return 1, Fore.YELLOW  # 中优先级，黄色
    elif '!' in todo_text:
        return 2, Fore.CYAN  # 低优先级，青色
    else:
        return 3, Fore.GREEN  # 普通优先级，绿色

def scan_todos(directory='.', extensions=None):
    """扫描指定目录下的文件，查找TODO注释"""
    if extensions is None:
        extensions = ['.py', '.js', '.html', '.css', '.md']
    
    todos = []
    
    # 遍历所有文件
    for ext in extensions:
        for path in Path(directory).glob(f'**/*{ext}'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        # 根据文件类型选择不同的注释格式
                        if ext == '.py':
                            match = re.search(r'#\s*TODO:\s*(.*)', line)
                        else:
                            match = re.search(r'//\s*TODO:\s*(.*)', line)
                        
                        if match:
                            todo_text = match.group(1).strip()
                            priority, color = get_priority(todo_text)
                            todos.append({
                                'path': str(path),
                                'line': i + 1,
                                'text': todo_text,
                                'priority': priority,
                                'color': color
                            })
            except Exception as e:
                print(f"无法读取文件 {path}: {e}", file=sys.stderr)
    
    # 按优先级排序
    todos.sort(key=lambda x: x['priority'])
    return todos

def print_todos(todos):
    """在控制台打印TODO列表"""
    if not todos:
        print("没有找到TODO注释")
        return
    
    print("\n找到的TODO列表（按优先级排序）：")
    print("=" * 80)
    
    for todo in todos:
        print(f"{todo['color']}{todo['path']}:{todo['line']}{Fore.RESET} {todo['text']}")
    
    print("=" * 80)
    print(f"总计: {len(todos)} 个TODO项")

def generate_markdown(todos, output_file="todo_report.md"):
    """生成Markdown格式的报告"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# TODO 报告\n\n")
        
        # 按优先级分组
        priority_names = {
            0: "高优先级 (!!!)",
            1: "中优先级 (!!)",
            2: "低优先级 (!)",
            3: "普通优先级"
        }
        
        for priority in sorted(priority_names.keys()):
            priority_todos = [t for t in todos if t['priority'] == priority]
            if priority_todos:
                f.write(f"## {priority_names[priority]}\n\n")
                for todo in priority_todos:
                    f.write(f"- **{todo['path']}:{todo['line']}** - {todo['text']}\n")
                f.write("\n")
        
        f.write(f"\n总计: {len(todos)} 个TODO项\n")
    
    print(f"Markdown报告已生成: {output_file}")

def main():
    """主函数"""
    print("开始扫描TODO注释...")
    
    # 获取命令行参数
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'
    
    todos = scan_todos(directory)
    print_todos(todos)
    
    # 生成Markdown报告
    generate_markdown(todos)

if __name__ == "__main__":
    main() 