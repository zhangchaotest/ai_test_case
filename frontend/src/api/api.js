import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000', // 指向 FastAPI 地址
    timeout: 120000 // 设长一点，Gemini 生成比较慢
});

export const getRequirements = () => api.get('/requirements');
export const generateCases = (id) => api.post(`/requirements/${id}/generate`);
export const getTestCases = (id) => api.get(`/requirements/${id}/cases`);