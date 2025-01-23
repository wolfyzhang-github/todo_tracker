#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TodoTagger AI分析功能演示脚本

该脚本模拟AI分析过程，生成示例分析结果，
用于展示TodoTagger的AI分析功能，无需实际调用API。
"""

import json
import time
import random
from typing import List, Dict, Any

# 示例技能库
SKILLS = [
    "Python", "JavaScript", "HTML/CSS", "React", "Vue", "Angular", 
    "Node.js", "Django", "Flask", "FastAPI", "SQL", "MongoDB",
    "Redis", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
    "Git", "CI/CD", "测试", "性能优化", "安全", "UI/UX设计",
    "RESTful API", "GraphQL", "WebSocket", "微服务", "消息队列"
]

# 示例挑战库
CHALLENGES = [
    "需要深入理解现有代码",
    "可能需要重构相关模块",
    "性能优化要求高",
    "需要考虑向后兼容性",
    "可能影响其他功能模块",
    "需要全面的测试覆盖",
    "文档需要同步更新",
    "可能存在安全风险",
    "用户体验需要特别关注",
    "多平台兼容性挑战",
    "数据一致性保证",
    "并发处理复杂",
    "需要考虑边界情况",
    "错误处理需要完善",
    "可能需要第三方库支持"
]

# 示例实现思路模板
APPROACH_TEMPLATES = [
    "使用{tech}实现{feature}，确保{aspect}",
    "基于现有{component}扩展，添加{feature}功能",
    "重构{component}以支持{feature}，注意{aspect}",
    "创建新的{component}类/模块，实现{feature}功能",
    "集成{tech}库，实现{feature}，优化{aspect}",
    "设计{pattern}模式解决{feature}问题，提高{aspect}"
]

# 技术/组件/方面词库
TECHS = ["React", "Vue", "Angular", "Node.js", "Express", "Django", "Flask", "SQLAlchemy", "Mongoose", "Redux", "Vuex"]
COMPONENTS = ["用户界面", "后端API", "数据模型", "认证系统", "缓存层", "数据库查询", "中间件", "工具函数", "配置系统"]
FEATURES = ["数据验证", "错误处理", "性能优化", "用户体验", "响应式设计", "状态管理", "数据一致性", "安全防护"]
ASPECTS = ["可维护性", "性能", "安全性", "用户体验", "代码可读性", "测试覆盖", "扩展性", "兼容性"]
PATTERNS = ["工厂", "单例", "观察者", "策略", "适配器", "装饰器", "代理", "组合", "命令", "模板方法"]

def generate_approach() -> str:
    """生成一个随机的实现思路"""
    template = random.choice(APPROACH_TEMPLATES)
    return template.format(
        tech=random.choice(TECHS),
        component=random.choice(COMPONENTS),
        feature=random.choice(FEATURES),
        aspect=random.choice(ASPECTS),
        pattern=random.choice(PATTERNS)
    )

def analyze_todo(todo: Dict[str, Any], todo_id: str) -> Dict[str, Any]:
    """生成一个TODO项的模拟分析结果"""
    # 基于内容和优先级确定复杂度
    content = todo['content'].lower()
    priority = todo['priority']
    
    # 根据内容长度和关键词判断复杂度
    length_factor = len(content) / 20  # 内容越长越复杂
    complexity_words = ["复杂", "difficult", "complex", "重构", "refactor", "优化", "optimize"]
    complexity_score = length_factor + sum(2 for word in complexity_words if word in content)
    
    # 优先级也影响复杂度评估
    priority_factor = {"critical": 1.5, "high": 1.2, "medium": 1.0, "low": 0.8, "normal": 1.0}
    complexity_score *= priority_factor.get(priority, 1.0)
    
    # 确定最终复杂度等级
    if complexity_score > 8:
        complexity = "复杂"
        hours = random.uniform(8, 24)
    elif complexity_score > 4:
        complexity = "中等"
        hours = random.uniform(3, 8)
    else:
        complexity = "简单"
        hours = random.uniform(0.5, 3)
    
    # 随机选择所需技能（根据内容关键词）
    skills_count = random.randint(2, 5)
    selected_skills = set()
    
    # 尝试根据内容选择相关技能
    tech_keywords = {
        "python": ["Python", "Django", "Flask", "FastAPI"],
        "js": ["JavaScript", "Node.js"],
        "react": ["React", "JavaScript"],
        "vue": ["Vue", "JavaScript"],
        "angular": ["Angular", "JavaScript"],
        "ui": ["HTML/CSS", "UI/UX设计"],
        "api": ["RESTful API", "GraphQL"],
        "database": ["SQL", "MongoDB", "Redis"],
        "性能": ["性能优化"],
        "安全": ["安全"],
        "测试": ["测试"],
        "deploy": ["Docker", "Kubernetes"]
    }
    
    for keyword, related_skills in tech_keywords.items():
        if keyword in content:
            selected_skills.add(random.choice(related_skills))
    
    # 补充随机技能直到达到目标数量
    while len(selected_skills) < skills_count:
        selected_skills.add(random.choice(SKILLS))
    
    # 随机选择潜在挑战
    challenges_count = random.randint(1, 3)
    selected_challenges = random.sample(CHALLENGES, challenges_count)
    
    # 生成实现思路
    implementation_approach = generate_approach()
    
    # 建议优先级（通常与原优先级相近）
    priority_shift = random.choices([-1, 0, 1], weights=[0.2, 0.6, 0.2])[0]
    priority_order = ["critical", "high", "medium", "low", "normal"]
    try:
        current_index = priority_order.index(priority)
        suggested_index = max(0, min(len(priority_order) - 1, current_index + priority_shift))
        suggested_priority = priority_order[suggested_index]
    except ValueError:
        suggested_priority = priority
    
    return {
        "todo_id": todo_id,
        "complexity": complexity,
        "estimated_hours": round(hours, 1),
        "implementation_approach": implementation_approach,
        "required_skills": list(selected_skills),
        "potential_challenges": selected_challenges,
        "suggested_priority": suggested_priority
    }

def generate_work_plan(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """生成一个模拟的工作计划"""
    # 根据优先级和复杂度排序
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "normal": 4}
    complexity_order = {"复杂": 2, "中等": 1, "简单": 0}
    
    def sort_key(analysis):
        return (
            priority_order.get(analysis["suggested_priority"], 999),
            complexity_order.get(analysis["complexity"], 0),
            -analysis["estimated_hours"]  # 工时长的优先
        )
    
    sorted_analyses = sorted(analyses, key=sort_key)
    todo_sequence = [analysis["todo_id"] for analysis in sorted_analyses]
    
    # 计算总工时
    total_hours = sum(analysis["estimated_hours"] for analysis in analyses)
    
    # 生成时间线（假设每天8小时）
    suggested_timeline = {}
    current_day = 1
    current_day_hours = 0
    
    for analysis in sorted_analyses:
        todo_id = analysis["todo_id"]
        hours = analysis["estimated_hours"]
        
        # 如果当前任务会导致当天超过8小时，则进入下一天
        if current_day_hours + hours > 8 and current_day_hours > 0:
            current_day += 1
            current_day_hours = 0
        
        suggested_timeline[todo_id] = f"第{current_day}天"
        current_day_hours += hours
        
        # 如果复杂任务占用大部分时间，也进入下一天
        if hours > 6:
            current_day += 1
            current_day_hours = 0
    
    # 生成依赖关系（随机生成一些依赖）
    dependencies = {}
    potential_dependencies = todo_sequence.copy()
    
    for i, todo_id in enumerate(todo_sequence):
        # 前面30%的任务没有依赖
        if i < len(todo_sequence) * 0.3:
            continue
            
        # 随机决定是否有依赖
        if random.random() < 0.4:
            # 只能依赖前面的任务
            possible_deps = potential_dependencies[:i]
            if possible_deps:
                deps_count = min(len(possible_deps), random.randint(1, 2))
                deps = random.sample(possible_deps, deps_count)
                dependencies[todo_id] = deps
    
    # 生成总结
    days_needed = max([int(timeline.replace("第", "").replace("天", "")) for timeline in suggested_timeline.values()])
    tasks_count = len(analyses)
    complex_tasks = sum(1 for a in analyses if a["complexity"] == "复杂")
    
    summary = (
        f"该项目包含{tasks_count}个待办任务，其中复杂任务{complex_tasks}个，"
        f"预计总工时约{round(total_hours, 1)}小时，建议分{days_needed}天完成。"
        f"建议优先处理高优先级任务，并注意任务间的依赖关系。"
    )
    
    return {
        "todo_sequence": todo_sequence,
        "estimated_total_hours": round(total_hours, 1),
        "suggested_timeline": suggested_timeline,
        "dependencies": dependencies,
        "summary": summary
    }

def analyze_todos(todos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析所有TODO并生成工作计划"""
    print("开始模拟AI分析...")
    
    # 分析每个TODO
    analyses = []
    for i, todo in enumerate(todos):
        print(f"正在分析第 {i+1}/{len(todos)} 个TODO: {todo['content'][:30]}...")
        todo_id = f"TODO_{i+1}"
        analysis = analyze_todo(todo, todo_id)
        analyses.append(analysis)
        time.sleep(0.2)  # 模拟API调用延迟
    
    # 生成工作计划
    print("正在生成工作计划...")
    work_plan = generate_work_plan(analyses)
    time.sleep(0.5)  # 模拟API调用延迟
    
    # 返回结果
    result = {
        "analyses": analyses,
        "work_plan": work_plan
    }
    
    return result

if __name__ == "__main__":
    # 测试TODO列表
    test_todos = [
        {
            "content": "实现用户登录功能",
            "file_path": "app/auth.py",
            "line_number": 45,
            "priority": "high"
        },
        {
            "content": "优化数据库查询性能",
            "file_path": "app/database.py",
            "line_number": 120,
            "priority": "medium"
        },
        {
            "content": "修复导航栏在移动设备上的显示问题",
            "file_path": "app/components/Navbar.js",
            "line_number": 78,
            "priority": "low"
        },
        {
            "content": "添加用户注册表单验证",
            "file_path": "app/forms/register.py",
            "line_number": 23,
            "priority": "normal"
        },
        {
            "content": "实现文件上传功能",
            "file_path": "app/api/upload.py",
            "line_number": 12,
            "priority": "high"
        }
    ]
    
    # 运行分析
    result = analyze_todos(test_todos)
    
    # 保存结果到文件
    with open("demo_ai_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"分析完成，结果已保存到 demo_ai_analysis.json") 