import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000', // 指向 FastAPI 地址
    timeout: 300000 // 设长一点，Gemini 生成比较慢
});

export const getRequirements = (params) => api.get('/requirements', { params });
export const getAllTestCases = (params) => api.get('/cases', { params });

// 批量更新测试用例状态方法
export const batchUpdateCaseStatus = (data) => api.put('/cases/batch_status', data);
