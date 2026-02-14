import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
});

export const fetchHealth = () => API.get("health/");
export const fetchExecutive = () => API.get("executive/");
export const fetchForecast = () => API.get("forecast/");
export const fetchImpact = () => API.get("impact/");
export const fetchGraph = () => API.get("graph/");
