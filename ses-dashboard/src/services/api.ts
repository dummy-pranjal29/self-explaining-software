import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
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
