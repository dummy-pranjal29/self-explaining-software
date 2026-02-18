import axios from "axios";

// Use relative path - Vite proxy will forward to Django backend
const API = axios.create({
  baseURL: "/api",
});

// Default project ID - could be changed by user in the UI
let currentProjectId = "default";

export const setProjectId = (projectId: string) => {
  currentProjectId = projectId;
};

export const getProjectId = () => currentProjectId;

// API v1 endpoints
export const fetchHealth = () =>
  API.get(`v1/health/?project=${currentProjectId}`);
export const fetchExecutive = () =>
  API.get(`v1/executive/?project=${currentProjectId}`);
export const fetchForecast = () =>
  API.get(`v1/forecast/?project=${currentProjectId}`);
export const fetchImpact = () =>
  API.get(`v1/impact/?project=${currentProjectId}`);
export const fetchGraph = () =>
  API.get(`v1/graph/?project=${currentProjectId}`);

// Project management (v1)
export const fetchProjects = () => API.get("v1/projects/");
export const createProject = (name: string) =>
  API.post("v1/projects/create/", { name });
export const deleteProject = (projectId: string) =>
  API.delete(`v1/projects/delete/${projectId}/`);

// AI Chat endpoint
export interface ChatRequest {
  question: string;
}

export interface ChatResponse {
  status: "success" | "error";
  response?: string;
  message?: string;
  question: string;
}

export const sendChatMessage = (question: string) =>
  API.post<ChatResponse>("v1/chat/", { question });
