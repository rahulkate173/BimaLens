import axios from 'axios';

const api = axios.create({
  baseURL: `${(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '')}/api/v1`,
  timeout: 60000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

export async function signUp(name, email, password) {
  const res = await api.post('/auth/signup', { name, email, password });
  return res.data;
}

export async function signIn(email, password) {
  const res = await api.post('/auth/login', { email, password });
  return res.data;
}

export async function signOut() {
  await api.post('/auth/logout');
}

export async function getCurrentAccount() {
  const res = await api.get('/auth/me');
  return res.data;
}

export async function updateAccount(name) {
  const res = await api.patch('/auth/me', { name });
  return res.data;
}

export async function updateNotificationPreferences(notifications) {
  const res = await api.patch('/auth/notifications', notifications);
  return res.data;
}

// ── Policy CRUD ──────────────────────────────────────────────

export async function uploadPolicy(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/policies/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return res.data;
}

export async function getPolicies() {
  const res = await api.get('/policies');
  return res.data;
}

export async function getPolicy(policyId) {
  const res = await api.get(`/policies/${policyId}`);
  return res.data;
}

export async function getPolicyStatus(policyId) {
  const res = await api.get(`/policies/${policyId}/status`);
  return res.data;
}

export async function getPolicyPdfLink(policyId, annotated = false) {
  const res = await api.get(`/policies/${policyId}/pdf-link`, { params: { annotated } });
  return res.data;
}

export async function getPolicyAnalysis(policyId) {
  const res = await api.get(`/policies/${policyId}/analysis`);
  return res.data;
}

export async function getAnnotatedPdf(policyId) {
  const { url } = await getPolicyPdfLink(policyId, true);
  const res = await axios.get(url, {
    responseType: 'blob',
    timeout: 60000,
  });
  return res.data;
}

// ── Ask / Chat ───────────────────────────────────────────────

export async function askQuestion(policyId, question, language = 'English') {
  const res = await api.post(`/policies/${policyId}/ask`, { question, language });
  return res.data;
}

export async function assessPolicyFit(policyId, profile) {
  const res = await api.post(`/policies/${policyId}/fit`, profile);
  return res.data;
}

export async function getClaimChecklist(policyId) {
  const res = await api.get(`/policies/${policyId}/claims`);
  return res.data;
}

export default api;
