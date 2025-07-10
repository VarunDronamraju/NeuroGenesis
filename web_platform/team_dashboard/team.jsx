import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

const TeamDashboard = () => {
  const [teams, setTeams] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchTeams(token);
    }
  }, []);

  const fetchTeams = async (token) => {
    try {
      const response = await axios.get('http://localhost:8000/teams', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTeams(response.data);
    } catch (err) {
      setError('Failed to fetch teams');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Team Dashboard</h1>
      {error && <p className="text-red-500">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {teams.map(team => (
          <div key={team.id} className="border p-4 rounded-lg">
            <h2 className="text-xl">{team.name}</h2>
            <p>{team.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TeamDashboard;
