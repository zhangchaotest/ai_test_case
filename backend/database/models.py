from pydantic import BaseModel
from typing import List, Optional, Dict, Any, TypeVar, Generic


# 需求模型
class Requirement(BaseModel):
    id: int
    module_name: str
    feature_name: str
    description: str
    priority: str
    case_count: int = 0 # 统计该需求下有多少用例

# 测试用例模型 (用于 API 返回)
class TestCaseResponse(BaseModel):
    id: int
    requirement_id: int
    case_title: str
    pre_condition: Optional[str] = ""
    steps: List[Dict[str, Any]] = []  # 给默认值 []
    expected_result: Optional[str] = ""

    # 允许这些字段为空，提供默认值
    priority: Optional[str] = "P1"
    case_type: Optional[str] = "Functional"
    test_data: Optional[Dict[str, Any]] = {}
    status: Optional[str] = "Active"

class PageResponse(BaseModel):
    total: int
    items: List[Any]


T = TypeVar('T')

# 通用的分页响应结构
class PageResponse(BaseModel, Generic[T]):
    total: int
    page: int
    size: int
    items: List[T]

