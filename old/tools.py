from old.database import get_db_connection

def save_feature(name: str, description: str) -> str:
    """
    将解析的需求功能点保存到数据库。
    
    参数:
        name (str): 功能点名称
        description (str): 功能点描述
        
    返回:
        str: 成功或错误信息
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO features (name, description, status) VALUES (?, ?, 'pending')", 
            (name, description)
        )
        conn.commit()
        conn.close()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"

def save_testcase(feature_id: int, title: str, steps: str, expected: str) -> str:
    """
    将生成的测试用例保存到数据库。
    
    参数:
        feature_id (int): 关联的功能点ID
        title (str): 测试用例标题
        steps (str): 测试步骤
        expected (str): 预期结果
        
    返回:
        str: 成功或错误信息
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO test_cases (feature_id, title, steps, expected, status) VALUES (?, ?, ?, ?, 'pending')",
            (feature_id, title, steps, expected)
        )
        conn.commit()
        conn.close()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"