import { describe, it, expect, vi, beforeEach } from "vitest";

// Use vi.hoisted to access mock functions before they're initialized
const { mockGet, mockPost, mockDelete, mockPut } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDelete: vi.fn(),
  mockPut: vi.fn(),
}));

vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({
      get: mockGet,
      post: mockPost,
      delete: mockDelete,
      put: mockPut,
    })),
  },
  create: vi.fn(() => ({
    get: mockGet,
    post: mockPost,
    delete: mockDelete,
    put: mockPut,
  })),
}));

// Import API service after mocking
import {
  fetchHealth,
  fetchForecast,
  fetchProjects,
  createProject,
  deleteProject,
  setProjectId,
  getProjectId,
} from "../services/api";

describe("API Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setProjectId("default");
  });

  describe("fetchHealth", () => {
    it("should fetch health data successfully", async () => {
      const mockHealthData = {
        timestamp: "2024-01-01T00:00:00Z",
        project_id: "test-project",
        health_score: 0.85,
      };

      mockGet.mockResolvedValueOnce({ data: mockHealthData });

      setProjectId("test-project");
      const result = await fetchHealth();

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("v1/health/"),
      );
      expect(result.data).toEqual(mockHealthData);
    });

    it("should handle health API errors gracefully", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      await expect(fetchHealth()).rejects.toThrow();
    });
  });

  describe("fetchForecast", () => {
    it("should fetch forecast data successfully", async () => {
      const mockForecastData = {
        timestamp: "2024-01-01T00:00:00Z",
        project_id: "test-project",
        forecast: {
          status: "success",
          forecast_next: 0.75,
          confidence_score: 0.85,
        },
        history: [],
      };

      mockGet.mockResolvedValueOnce({ data: mockForecastData });

      setProjectId("test-project");
      const result = await fetchForecast();

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("v1/forecast/"),
      );
      expect(result.data).toEqual(mockForecastData);
    });

    it("should return insufficient_data status when no history", async () => {
      const mockEmptyData = {
        timestamp: "2024-01-01T00:00:00Z",
        project_id: "test-project",
        forecast: {
          status: "insufficient_data",
        },
        history: [],
      };

      mockGet.mockResolvedValueOnce({ data: mockEmptyData });

      const result = await fetchForecast();

      expect(result.data.forecast.status).toBe("insufficient_data");
    });
  });

  describe("Project Management", () => {
    it("should list all projects", async () => {
      const mockProjects = {
        projects: ["project-1", "project-2"],
        count: 2,
      };

      mockGet.mockResolvedValueOnce({ data: mockProjects });

      const result = await fetchProjects();

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("v1/projects/"),
      );
      expect(result.data.projects).toEqual(["project-1", "project-2"]);
    });

    it("should create a new project", async () => {
      const mockCreatedProject = {
        project_id: "new-project-id",
        name: "New Project",
        status: "created",
      };

      mockPost.mockResolvedValueOnce({
        data: mockCreatedProject,
      });

      const result = await createProject("New Project");

      expect(mockPost).toHaveBeenCalled();
      expect(result.data.status).toBe("created");
    });

    it("should delete a project", async () => {
      const mockDeleteResult = {
        project_id: "project-to-delete",
        status: "deleted",
      };

      mockDelete.mockResolvedValueOnce({
        data: mockDeleteResult,
      });

      const result = await deleteProject("project-to-delete");

      expect(mockDelete).toHaveBeenCalled();
      expect(result.data.status).toBe("deleted");
    });
  });

  describe("Project ID Management", () => {
    it("should set and get current project ID", () => {
      setProjectId("custom-project");
      expect(getProjectId()).toBe("custom-project");
    });

    it("should default to 'default' project", () => {
      expect(getProjectId()).toBe("default");
    });
  });
});

describe("API Response Types", () => {
  it("should have correct health response structure", () => {
    const mockResponse = {
      timestamp: "2024-01-01T00:00:00Z",
      project_id: "test",
      health_score: 0.85,
      component_scores: {
        stability: 0.9,
        complexity: 0.8,
      },
    };

    expect(mockResponse).toHaveProperty("timestamp");
    expect(mockResponse).toHaveProperty("project_id");
    expect(mockResponse).toHaveProperty("health_score");
  });

  it("should have correct forecast response structure", () => {
    const mockResponse = {
      timestamp: "2024-01-01T00:00:00Z",
      project_id: "test",
      history: [{ timestamp: "2024-01-01T00:00:00Z", health_score: 0.9 }],
      forecast: {
        status: "success",
        forecast_next: 0.75,
        confidence_score: 0.85,
        confidence_interval: {
          lower: 0.65,
          upper: 0.85,
        },
      },
    };

    expect(mockResponse).toHaveProperty("history");
    expect(mockResponse).toHaveProperty("forecast");
    expect(mockResponse.forecast).toHaveProperty("status");
    expect(mockResponse.forecast).toHaveProperty("forecast_next");
  });
});
