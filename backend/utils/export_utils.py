#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：ai_test_case_fast 
@File    ：export_utils.py
@Author  ：张超
@Date    ：2025/12/25 15:06
@Desc    ：
"""
import pandas as pd
import xmind
import os
import tempfile
from io import BytesIO


def generate_excel(data: list) -> BytesIO:
    """
    生成 Excel，严格控制列顺序
    格式：模块 | 标题 | 优先级 | 前置条件 | 操作步骤 | 预期结果
    """
    if not data:
        return BytesIO()

    # 1. 准备数据，只取需要的字段
    excel_data = []
    for item in data:
        excel_data.append({
            '所属模块': item['module_name'],
            '用例标题': item['case_title'],
            '优先级': item['priority'],
            '前置条件': item['pre_condition'],
            '操作步骤': item['excel_steps'],  # 使用在 db 层格式化好的字符串
            '预期结果': item['expected_result'],
            '类型': item['case_type']
        })

    # 2. 创建 DataFrame
    df = pd.DataFrame(excel_data)

    # 3. 🔥 强制指定列顺序 (这是你要求的格式)
    columns_order = ['所属模块', '用例标题', '优先级', '前置条件', '操作步骤', '预期结果', '类型']
    df = df[columns_order]

    # 4. 写入 Excel 流
    output = BytesIO()
    # engine='xlsxwriter' 支持更好的格式控制（自动换行等），如果没有安装，用 openpyxl 也可以
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='测试用例')

        # 简单的列宽调整 (依赖 openpyxl)
        worksheet = writer.sheets['测试用例']
        # 设置列宽
        worksheet.column_dimensions['A'].width = 15  # 模块
        worksheet.column_dimensions['B'].width = 30  # 标题
        worksheet.column_dimensions['D'].width = 20  # 前置
        worksheet.column_dimensions['E'].width = 50  # 步骤 (宽一点)
        worksheet.column_dimensions['F'].width = 30  # 预期

        # 设置自动换行 (需要遍历单元格，略繁琐，这里暂略，Excel打开后手动点自动换行即可)

    output.seek(0)
    return output


# backend/utils/export_utils.py

def generate_markdown(data: list) -> BytesIO:
    """
    生成符合 XMind 导入结构的 Markdown
    结构：
    # 根节点
    ## 模块名
    ### 用例标题 [优先级]
    - 前置条件：xxx
    - 1. 步骤 (预期: xxx)
    - 2. 步骤 (预期: xxx)
    - 预期结果: 总结 xxx
    """
    content = "# AI生成测试用例集\n\n"

    # 1. 按模块分组
    modules = {}
    for row in data:
        mod = row['module_name']
        if mod not in modules: modules[mod] = []
        modules[mod].append(row)

    # 2. 构建内容
    for mod_name, cases in modules.items():
        # Level 2: 模块 (XMind 主分支)
        content += f"## {mod_name}\n\n"

        for case in cases:
            title = case['case_title']
            prio = case['priority']
            pre = case['pre_condition']
            final_expect = case['expected_result']
            steps = case['md_steps']  # 这是一个列表 ['1. xxx', '2. xxx']

            # Level 3: 用例标题 (XMind 子主题)
            content += f"### {title} [{prio}]\n"

            # Level 4: 详情节点 (列表项)

            # 1. 前置条件节点
            if pre and pre != "无":
                content += f"- 前置条件：{pre}\n"

            # 2. 步骤节点 (直接作为子节点展开)
            if steps:
                for step_str in steps:
                    content += f"- {step_str}\n"

            # 3. 总体预期结果节点 (为了不混淆，放在最后)
            # 如果步骤里已经包含了详细预期，这里的总体预期可以作为总结
            if final_expect and final_expect != "无":
                # 处理一下换行，确保缩进对其
                clean_expect = final_expect.replace('\n', '；')
                content += f"- 预期结果: {clean_expect}\n"

            content += "\n"  # 用例间空行

    # 3. 转二进制流
    output = BytesIO()
    output.write(content.encode('utf-8'))
    output.seek(0)
    return output

def generate_csv(data: list) -> BytesIO:
    """生成 CSV 文件流"""
    df = pd.DataFrame(data)

    rename_map = {
        'module_name': '所属模块',
        'case_title': '用例标题',
        'pre_condition': '前置条件',
        'steps_str': '步骤',
        'expected_result': '预期结果',
        'case_type': '用例类型',
        'priority': '优先级'
    }

    cols = [c for c in rename_map.keys() if c in df.columns]
    df = df[cols].rename(columns=rename_map)

    output = BytesIO()
    # utf-8-sig 用于解决 Excel 打开 CSV 中文乱码问题
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return output


def generate_xmind(data: list) -> str:
    """
    生成 XMind 文件
    注意：xmind 库需要生成物理文件，所以我们返回临时文件路径
    """
    # 1. 创建临时文件路径
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "test_cases.xmind")

    # 如果文件存在先删除
    if os.path.exists(file_path):
        os.remove(file_path)

    # 2. 加载工作簿
    workbook = xmind.load(file_path)
    sheet = workbook.getPrimarySheet()
    sheet.setTitle("测试用例集")

    # 根节点
    root = sheet.getRootTopic()
    root.setTitle("AI生成测试用例")

    # 3. 按模块分组数据
    modules = {}
    for row in data:
        mod = row.get('module_name') or '未分类'
        if mod not in modules:
            modules[mod] = []
        modules[mod].append(row)

    # 4. 构建思维导图结构
    for mod_name, cases in modules.items():
        # 一级节点：模块
        mod_topic = root.addSubTopic()
        mod_topic.setTitle(mod_name)

        for case in cases:
            # 二级节点：用例标题
            case_topic = mod_topic.addSubTopic()
            case_topic.setTitle(case['case_title'])

            # 🔥 优先级标记 (Markers)
            # xmind 库通常支持 priority-1 (红色旗子) 到 priority-9
            prio = case.get('priority', 'P1')
            if prio == 'P0':
                case_topic.addMarker("priority-1")
            elif prio == 'P1':
                case_topic.addMarker("priority-2")
            elif prio == 'P2':
                case_topic.addMarker("priority-3")

            # 三级节点：前置条件 (如果有)
            if case.get('pre_condition') and case.get('pre_condition') != '无':
                pre_topic = case_topic.addSubTopic()
                pre_topic.setTitle(f"前置: {case['pre_condition']}")

            # 三级节点：步骤 (把步骤详情放这里)
            # 或者把步骤放在 Notes 备注里，为了直观我们作为子节点
            steps_content = case.get('steps_str', '')
            if steps_content:
                # 简单处理：把步骤作为一大段文本放一个节点，或者拆分
                step_topic = case_topic.addSubTopic()
                step_topic.setTitle(steps_content)
                # 也可以设置折叠
                # step_topic.setFolded()

            # 三级节点：预期结果
            exp_topic = case_topic.addSubTopic()
            exp_topic.setTitle(f"预期: {case['expected_result']}")

    # 5. 保存文件
    xmind.save(workbook, file_path)
    return file_path


