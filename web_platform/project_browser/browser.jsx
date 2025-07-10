import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ProjectBrowser = () => {
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchProjects(token);
    }
  }, []);

  const fetchProjects = async (token) => {
    try {
      const response = await axios.get('http://localhost:8000/projects', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(response.data);
    } catch (err) {
      setError('Failed to fetch projects');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Project Browser</h1>
      {error && <p className="text-red-500">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {projects.map(project => (
          <div key={project.project_id} className="border p-4 rounded-lg">
            <h2 className="text-xl">{project.project_id}</h2>
            <p>{project.description}</p>
            <p>Last Modified: {new Date(project.last_modified).toLocaleDateString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProjectBrowser;
