// src/components/LoginPage.js
import React, { useState } from 'react';
import axios from 'axios';

const LoginPage = () => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [token, setToken] = useState(null);

  const handleChange = (e) => {
    setFormData({ 
      ...formData, 
      [e.target.name]: e.target.value 
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await axios.post('http://localhost:8000/api/login/', formData);
      const { access, username } = response.data;
      localStorage.setItem('accessToken', access); 
      setToken(access);
      alert(`Welcome, ${username}!`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '100px auto' }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Username</label><br />
          <input 
            type="text" 
            name="username" 
            value={formData.username}
            onChange={handleChange} 
            required 
          />
        </div>
        <div style={{ marginTop: 10 }}>
          <label>Password</label><br />
          <input 
            type="password" 
            name="password" 
            value={formData.password}
            onChange={handleChange} 
            required 
          />
        </div>
        <button type="submit" style={{ marginTop: 20 }}>Login</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {token && <p style={{ color: 'green' }}>Logged in! Token saved.</p>}
    </div>
  );
};

export default LoginPage;
