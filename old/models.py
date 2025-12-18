from pydantic import BaseModel
from typing import List, Optional

class TextInput(BaseModel):
    # 文本输入模型
    text: str

class IdList(BaseModel):
    # ID列表模型
    ids: List[int]

class GenerateInput(BaseModel):
    # 生产输入模型
    feature_ids: List[int]

class Feature(BaseModel):
    # 功能点模型
    id: Optional[int] = None
    name: str
    description: str
    status: Optional[str] = "pending"

class TestCase(BaseModel):
    # 测试用例模型
    id: Optional[int] = None
    feature_id: int
    title: str
    steps: str
    expected: str
    status: Optional[str] = "pending"