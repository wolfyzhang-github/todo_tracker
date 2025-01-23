#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析器模块

该模块负责调用AI API（如Azure OpenAI, OpenAI API或本地部署的模型）
来分析TODO项的复杂度、工作量和实现思路，并生成工作计划。
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
import requests
from dataclasses import dataclass, asdict
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ai_analyzer')

@dataclass
class AIConfig:
    """AI配置"""
    provider: str  # openai, azure, qwen_local
    api_key: str
    api_base: str
    api_version: str = ""
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.3
    proxy: str = ""
    
    @classmethod
    def from_env(cls) -> 'AIConfig':
        """从环境变量加载配置"""
        return cls(
            provider=os.environ.get('TODO_AI_PROVIDER', 'openai'),
            api_key=os.environ.get('TODO_AI_API_KEY', ''),
            api_base=os.environ.get('TODO_AI_API_BASE', 'https://api.openai.com/v1'),
            api_version=os.environ.get('TODO_AI_API_VERSION', ''),
            model=os.environ.get('TODO_AI_MODEL', 'gpt-3.5-turbo'),
            max_tokens=int(os.environ.get('TODO_AI_MAX_TOKENS', 1000)),
            temperature=float(os.environ.get('TODO_AI_TEMPERATURE', 0.3)),
            proxy=os.environ.get('TODO_AI_PROXY', '')
        )
    
    @classmethod
    def from_file(cls, path: str) -> 'AIConfig':
        """从配置文件加载"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f).get('ai_config', {})
                return cls(
                    provider=config_data.get('provider', 'openai'),
                    api_key=config_data.get('api_key', ''),
                    api_base=config_data.get('api_base', 'https://api.openai.com/v1'),
                    api_version=config_data.get('api_version', ''),
                    model=config_data.get('model', 'gpt-3.5-turbo'),
                    max_tokens=int(config_data.get('max_tokens', 1000)),
                    temperature=float(config_data.get('temperature', 0.3)),
                    proxy=config_data.get('proxy', '')
                )
        except Exception as e:
            logger.error(f"读取AI配置文件失败: {e}")
            return cls.from_env()


@dataclass
class TodoAnalysis:
    """单个TODO项的分析结果"""
    todo_id: str
    complexity: str  # 简单/中等/复杂
    estimated_hours: float
    implementation_approach: str
    required_skills: List[str]
    potential_challenges: List[str]
    suggested_priority: str
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class WorkPlan:
    """工作计划"""
    todo_sequence: List[str]  # TODO项ID的建议处理顺序
    estimated_total_hours: float
    suggested_timeline: Dict[str, str]  # TODO ID -> 建议时间（例如"第1天"）
    dependencies: Dict[str, List[str]]  # TODO ID -> 依赖的其他TODO ID列表
    summary: str
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


class AIAnalyzer:
    """AI分析器，负责调用AI API分析TODO项"""
    
    def __init__(self, config: Optional[AIConfig] = None, 
                 config_path: str = "todo_config.json"):
        """初始化AI分析器"""
        if config:
            self.config = config
        else:
            # 先尝试从配置文件加载
            self.config = AIConfig.from_file(config_path)
            # 如果没有API密钥，则从环境变量加载
            if not self.config.api_key:
                self.config = AIConfig.from_env()
        
        # 设置代理
        self.session = requests.Session()
        if self.config.proxy:
            self.session.proxies = {
                "http": self.config.proxy,
                "https": self.config.proxy
            }
    
    def _read_file_context(self, file_path: str, line_number: int, 
                          context_lines: int = 30) -> str:
        """读取文件中TODO周围的代码作为上下文"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # 计算上下文范围
                start_line = max(0, line_number - context_lines - 1)
                end_line = min(len(lines), line_number + context_lines)
                
                # 提取上下文
                context = ''.join(lines[start_line:end_line])
                return context
        except Exception as e:
            logger.error(f"读取文件上下文失败: {e}")
            return ""
    
    def _call_openai_api(self, messages: List[Dict[str, str]]) -> Dict:
        """调用OpenAI API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"调用OpenAI API失败: {e}")
            if hasattr(response, 'text'):
                logger.error(f"响应内容: {response.text}")
            return {"error": str(e)}
    
    def _call_azure_api(self, messages: List[Dict[str, str]]) -> Dict:
        """调用Azure OpenAI API"""
        headers = {
            "Content-Type": "application/json",
            "api-key": self.config.api_key
        }
        
        payload = {
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/openai/deployments/{self.config.model}/chat/completions?api-version={self.config.api_version}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"调用Azure API失败: {e}")
            if hasattr(response, 'text'):
                logger.error(f"响应内容: {response.text}")
            return {"error": str(e)}
    
    def _call_qwen_local(self, messages: List[Dict[str, str]]) -> Dict:
        """调用本地部署的Qwen模型API"""
        headers = {
            "Content-Type": "application/json"
        }
        
        # 如果有API密钥
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        try:
            response = self.session.post(
                f"{self.config.api_base}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"调用Qwen API失败: {e}")
            if hasattr(response, 'text'):
                logger.error(f"响应内容: {response.text}")
            return {"error": str(e)}
    
    def _call_ai_api(self, messages: List[Dict[str, str]]) -> str:
        """根据配置调用相应的AI API"""
        response = {"error": "未知提供商"}
        
        if self.config.provider.lower() == 'openai':
            response = self._call_openai_api(messages)
        elif self.config.provider.lower() == 'azure':
            response = self._call_azure_api(messages)
        elif self.config.provider.lower() == 'qwen_local':
            response = self._call_qwen_local(messages)
        else:
            logger.error(f"不支持的AI提供商: {self.config.provider}")
            return ""
        
        # 处理错误
        if "error" in response:
            logger.error(f"AI API返回错误: {response['error']}")
            return ""
        
        # 提取回复内容
        try:
            content = response["choices"][0]["message"]["content"]
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"解析API响应失败: {e}")
            return ""
    
    def analyze_todo(self, todo_id: str, todo_content: str, file_path: str, 
                    line_number: int, priority: str) -> Optional[TodoAnalysis]:
        """分析单个TODO项"""
        # 读取文件上下文
        context = self._read_file_context(file_path, line_number)
        
        # 构建提示
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的软件开发顾问，擅长分析代码任务并估计工作量。
请根据提供的TODO注释和代码上下文，分析：
1. 复杂度（简单/中等/复杂）
2. 预估工作时间（小时）
3. 实现思路
4. 所需技能
5. 潜在挑战
6. 建议优先级（考虑提供的现有优先级和你的分析）

请用JSON格式回复，包含以下字段：
{
  "complexity": "简单|中等|复杂",
  "estimated_hours": 数字,
  "implementation_approach": "简短描述实现思路",
  "required_skills": ["技能1", "技能2", ...],
  "potential_challenges": ["挑战1", "挑战2", ...],
  "suggested_priority": "紧急|高|中|低|普通"
}
只返回JSON，不要有其他解释。"""
            },
            {
                "role": "user",
                "content": f"""TODO内容: {todo_content}
文件路径: {file_path}
行号: {line_number}
当前优先级: {priority}

代码上下文:
```
{context}
```

请分析这个TODO任务的复杂度、工作量和实现思路。"""
            }
        ]
        
        # 调用AI API获取分析
        result = self._call_ai_api(messages)
        
        # 解析返回的JSON
        if result:
            try:
                data = json.loads(result)
                return TodoAnalysis(
                    todo_id=todo_id,
                    complexity=data.get("complexity", "未知"),
                    estimated_hours=float(data.get("estimated_hours", 0)),
                    implementation_approach=data.get("implementation_approach", ""),
                    required_skills=data.get("required_skills", []),
                    potential_challenges=data.get("potential_challenges", []),
                    suggested_priority=data.get("suggested_priority", priority)
                )
            except json.JSONDecodeError:
                logger.error(f"无法解析AI返回的JSON: {result}")
            except Exception as e:
                logger.error(f"处理AI分析结果时出错: {e}")
        
        return None
    
    def generate_work_plan(self, todo_analyses: List[TodoAnalysis]) -> Optional[WorkPlan]:
        """根据所有TODO项的分析结果生成工作计划"""
        if not todo_analyses:
            return None
        
        # 构建提示
        todos_json = json.dumps([t.to_dict() for t in todo_analyses], ensure_ascii=False, indent=2)
        
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的项目管理顾问，擅长规划软件开发工作。
根据提供的TODO任务分析列表，生成一个合理的工作计划。
考虑每个任务的复杂度、工作量、优先级和可能的依赖关系。

请用JSON格式回复，包含以下字段：
{
  "todo_sequence": ["todo_id1", "todo_id2", ...],
  "estimated_total_hours": 数字,
  "suggested_timeline": {"todo_id1": "建议完成时间", ...},
  "dependencies": {"todo_id1": ["依赖的todo_id"], ...},
  "summary": "工作计划总结"
}
只返回JSON，不要有其他解释。"""
            },
            {
                "role": "user",
                "content": f"""以下是所有TODO任务的分析结果：

{todos_json}

请根据这些分析结果，生成一个合理的工作计划，包括任务的处理顺序、
总工作量、时间线、任务间的依赖关系，以及计划总结。"""
            }
        ]
        
        # 调用AI API获取工作计划
        result = self._call_ai_api(messages)
        
        # 解析返回的JSON
        if result:
            try:
                data = json.loads(result)
                return WorkPlan(
                    todo_sequence=data.get("todo_sequence", []),
                    estimated_total_hours=float(data.get("estimated_total_hours", 0)),
                    suggested_timeline=data.get("suggested_timeline", {}),
                    dependencies=data.get("dependencies", {}),
                    summary=data.get("summary", "")
                )
            except json.JSONDecodeError:
                logger.error(f"无法解析AI返回的JSON: {result}")
            except Exception as e:
                logger.error(f"处理AI工作计划结果时出错: {e}")
        
        return None


def analyze_todos(todos: List[Dict], config_path: str = "todo_config.json") -> Dict:
    """分析所有TODO项并生成工作计划"""
    # 初始化AI分析器
    analyzer = AIAnalyzer(config_path=config_path)
    
    # 分析每个TODO项
    todo_analyses = []
    for i, todo in enumerate(todos):
        logger.info(f"正在分析 TODO {i+1}/{len(todos)}: {todo['content'][:30]}...")
        
        # 生成唯一ID
        todo_id = f"TODO_{i+1}"
        
        # 分析TODO
        analysis = analyzer.analyze_todo(
            todo_id=todo_id,
            todo_content=todo['content'],
            file_path=todo['file_path'],
            line_number=todo['line_number'],
            priority=todo['priority']
        )
        
        if analysis:
            todo_analyses.append(analysis)
            
            # 避免API限制
            if i < len(todos) - 1:
                time.sleep(1)
    
    # 生成工作计划
    logger.info("正在生成工作计划...")
    work_plan = analyzer.generate_work_plan(todo_analyses)
    
    # 组合结果
    result = {
        "analyses": [a.to_dict() for a in todo_analyses] if todo_analyses else [],
        "work_plan": work_plan.to_dict() if work_plan else {}
    }
    
    return result


if __name__ == "__main__":
    # 测试分析器
    import sys
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "todo_config.json"
    
    # 测试TODO
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
        }
    ]
    
    # 运行分析
    result = analyze_todos(test_todos, config_file)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 