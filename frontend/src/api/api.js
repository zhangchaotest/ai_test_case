import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000', // 指向 FastAPI 地址
    timeout: 300000 // 设长一点，Gemini 生成比较慢
});

export const BASE_URL = 'http://localhost:8000'

export const getRequirements = (params) => api.get('/requirements', { params });
export const getAllTestCases = (params) => api.get('/cases', { params });

// 批量更新测试用例状态方法
export const batchUpdateCaseStatus = (data) => api.put('/cases/batch_status', data);


// 获取项目列表
export const getProjects = () => api.get('/projects');

// 获取需求拆解结果列表 (ProTable 用)
export const getBreakdownList = (params) => api.get('/requirement_breakdown', { params });

// 更新单个功能点
export const updateBreakdownItem = (id, data) => api.put(`/requirement_breakdown/${id}`, data);
// 批量更新功能点状态
export const batchUpdateBreakdownStatus = (data) => api.put('/requirement_breakdown/batch_status', data);
export const updateBreakdownStatus =(id,status) =>api.put(`/requirement_breakdown/${id}/status`,{status})