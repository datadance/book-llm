import inspect
import traceback
from copy import deepcopy
from pprint import pformat
from types import GenericAlias
from typing import get_origin, Annotated

_TOOL_HOOKS = {}  # 存储注册的工具函数
_TOOL_DESCRIPTIONS = {}  # 存储工具函数的描述信息

# 工具注册代码
def register_tool(func: callable):
    tool_name = func.__name__  # 获取函数的名称
    tool_description = inspect.getdoc(func).strip()  # 获取函数的文档字符串，并去除首尾空白字符
    python_params = inspect.signature(func).parameters  # 获取函数的参数信息
    tool_params = []  # 存储工具函数的参数信息
    for name, param in python_params.items():
        annotation = param.annotation  # 获取参数的类型注解
        if annotation is inspect.Parameter.empty:  # 检查参数是否有类型注解
            raise TypeError(f"Parameter `{name}` missing type annotation")
        if get_origin(annotation) != Annotated:  # 检查类型注解是否为 typing.Annotated
            raise TypeError(f"Annotation type for `{name}` must be typing.Annotated")

        typ, (description, required) = annotation.__origin__, annotation.__metadata__  # 获取类型注解的原始类型和元数据
        typ: str = str(typ) if isinstance(typ, GenericAlias) else typ.__name__  # 获取类型注解的名称
        if not isinstance(description, str):  # 检查描述信息是否为字符串类型
            raise TypeError(f"Description for `{name}` must be a string")
        if not isinstance(required, bool):  # 检查是否必需参数的标志是否为布尔类型
            raise TypeError(f"Required for `{name}` must be a bool")

        tool_params.append({
            "name": name,
            "description": description,
            "type": typ,
            "required": required
        })  # 将参数信息添加到工具函数的参数列表中
    tool_def = {
        "name": tool_name,
        "description": tool_description,
        "params": tool_params
    }  # 构建工具函数的定义信息

    print("[registered tool] " + pformat(tool_def))  # 打印注册的工具函数信息
    _TOOL_HOOKS[tool_name] = func  # 将工具函数添加到工具函数字典中
    _TOOL_DESCRIPTIONS[tool_name] = tool_def  # 将工具函数的定义信息添加到工具函数描述字典中

    return func


def dispatch_tool(tool_name: str, tool_params: dict) -> str:
    if tool_name not in _TOOL_HOOKS:
        return f"Tool `{tool_name}` not found. Please use a provided tool."  # 如果指定的工具函数不存在，则返回错误信息
    tool_call = _TOOL_HOOKS[tool_name]  # 获取工具函数的调用对象
    try:
        ret = tool_call(**tool_params)  # 调用工具函数，并传递参数
    except:
        ret = traceback.format_exc()
    return str(ret)  # 返回工具函数的执行结果

# 查看已注册的工具
def get_tools() -> dict:
    return deepcopy(_TOOL_DESCRIPTIONS)
