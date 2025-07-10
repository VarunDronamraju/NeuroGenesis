import React, { useState } from 'react';
import axios from 'axios';

const SettingsPanel = () => {
  const [profile, setProfile] = useState({ full_name: '', organization: '', bio: '' });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const saveSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.put('http://localhost:8000/users/profile', profile, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('Profile updated successfully');
    } catch (err) {
      setError('Failed to update profile');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Settings</h1>
      {error && <p className="text-red-500">{error}</p>}
      <div className="space-y-4">
        <input
          type="text"
          name="full_name"
          value={profile.full_name}
          onChange={handleChange}
          placeholder="Full Name"
          className="border p-2 w-full"
        />
        <input
          type="text"
          name="organization"
          value={profile.organization}
          onChange={handleChange}
          placeholder="Organization"
          className="border p-2 w-full"
        />
        <textarea
          name="bio"
          value={profile.bio}
          onChange={handleChange}
          placeholder="Bio"
          className="border p-2 w-full"
        />
        <button onClick={saveSettings} className="bg-blue-500 text-white p-2 rounded">
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default SettingsPanel;
