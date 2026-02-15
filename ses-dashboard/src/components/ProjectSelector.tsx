import { useState, useEffect } from "react";
import { fetchProjects, setProjectId } from "../services/api";

interface Project {
  project_id: string;
  name?: string;
}

function toProjectList(projects: string[]): Project[] {
  return projects.map((id) => ({ project_id: id }));
}

interface ProjectSelectorProps {
  onProjectChange?: () => void;
}

export default function ProjectSelector({
  onProjectChange,
}: ProjectSelectorProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("default");
  const [isLoading, setIsLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  // Load projects and restore selected project from localStorage on mount
  useEffect(() => {
    const loadProjects = async () => {
      try {
        // First, restore from localStorage
        const stored = localStorage.getItem("ses_selected_project");
        if (stored) {
          setSelectedProject(stored);
          setProjectId(stored);
        }

        // Then fetch projects list
        const response = await fetchProjects();
        const projectList = response.data.projects || [];

        // Ensure 'default' is in the list
        if (!projectList.includes("default")) {
          projectList.unshift("default");
        }

        setProjects(toProjectList(projectList));
      } catch (error) {
        console.error("Failed to load projects:", error);
        // Fallback to default
        setProjects([{ project_id: "default" }]);
      } finally {
        setIsLoading(false);
      }
    };

    loadProjects();
  }, []);

  const handleProjectChange = async (projectId: string) => {
    setSelectedProject(projectId);
    setProjectId(projectId);
    localStorage.setItem("ses_selected_project", projectId);
    setIsOpen(false);

    // Trigger data reload for all dashboard components
    if (onProjectChange) {
      onProjectChange();
    } else {
      // Default behavior: reload the page
      window.location.reload();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-neutral-500 text-sm">
        <div className="w-4 h-4 border border-neutral-600 rounded animate-spin border-t-transparent" />
        Loading...
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-neutral-900 border border-neutral-700 rounded-lg hover:border-neutral-500 transition-colors text-sm"
      >
        <svg
          className="w-4 h-4 text-neutral-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
          />
        </svg>
        <span className="text-neutral-200">{selectedProject}</span>
        <svg
          className={`w-4 h-4 text-neutral-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-56 bg-neutral-900 border border-neutral-700 rounded-lg shadow-xl z-20 overflow-hidden">
            <div className="p-2 border-b border-neutral-800">
              <span className="text-xs text-neutral-500 uppercase tracking-wider">
                Select Project
              </span>
            </div>
            <div className="max-h-60 overflow-y-auto py-1">
              {projects.map((project) => (
                <button
                  key={project.project_id}
                  onClick={() => handleProjectChange(project.project_id)}
                  className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                    selectedProject === project.project_id
                      ? "bg-indigo-600/20 text-indigo-400"
                      : "text-neutral-300 hover:bg-neutral-800"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono">{project.project_id}</span>
                    {selectedProject === project.project_id && (
                      <svg
                        className="w-4 h-4 text-indigo-400"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
