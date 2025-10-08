import React, { useState } from 'react';
import axios from 'axios';
import { Settings, LogOut, ArrowLeft, Mail } from 'lucide-react';

const UserProfile = ({ onClose }) => {
  const user = {
    name: 'ASH',
    email: 'ash@personalai.com',
    avatar: '/ms.jpg',
    user_id: 'user_001', // ✅ Replace with actual user_id from your auth system
  };

  const [gmail, setGmail] = useState('');
  const [appPassword, setAppPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleLogout = () => {
    alert('Logging out...');
    window.location.reload();
  };

  // ✅ Function to save Gmail credentials securely
  const handleSaveGmail = async () => {
    if (!gmail || !appPassword) {
      setMessage('⚠️ Please enter both email and app password.');
      return;
    }
    try {
      const res = await axios.post('http://localhost:8000/api/users/save_email', {
        user_id: user.user_id,
        email: gmail,
        app_password: appPassword,
      });
      setMessage(res.data.message);
    } catch (error) {
      console.error(error);
      setMessage('❌ Failed to save Gmail settings.');
    }
  };

  return (
    <div className="userProfile h-full p-6 bg-gray-50 dark:bg-gray-800 flex flex-col items-center justify-center">
      <div className="w-full max-w-sm rounded-lg shadow-lg p-6 bg-white dark:bg-gray-700 relative">
        <button
          onClick={onClose}
          className="absolute top-4 left-4 p-2 rounded-full text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          title="Go back"
        >
          <ArrowLeft size={24} />
        </button>

        {/* --- Profile Section --- */}
        <div className="flex flex-col items-center mt-4 mb-6">
          <img
            src={user.avatar}
            alt="User Avatar"
            className="w-24 h-24 rounded-full border-4 border-purple-500 shadow-md"
          />
          <h3 className="mt-4 text-2xl font-bold dark:text-white">{user.name}</h3>
          <p className="text-gray-500 dark:text-gray-400">{user.email}</p>
        </div>

        {/* --- Settings Section --- */}
        <div className="border-t border-gray-200 dark:border-gray-600 py-4">
          <div className="flex items-center justify-between mb-4">
            <span className="flex items-center text-gray-700 dark:text-gray-200 font-semibold">
              <Settings size={20} className="mr-2" />
              Settings
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">Manage account</span>
          </div>
          <p className="text-gray-600 dark:text-gray-300 text-sm">
            Customize your experience and manage your personal data.
          </p>
        </div>

        {/* --- Gmail Configuration Section --- */}
        <div className="border-t border-gray-200 dark:border-gray-600 py-4 mt-4">
          <h4 className="flex items-center text-lg font-semibold text-gray-700 dark:text-gray-100 mb-3">
            <Mail size={20} className="mr-2 text-purple-500" />
            Configure Gmail
          </h4>

          <input
            type="email"
            placeholder="Enter your Gmail address"
            value={gmail}
            onChange={(e) => setGmail(e.target.value)}
            className="w-full mb-3 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-purple-500"
          />

          <input
            type="password"
            placeholder="Enter your App Password"
            value={appPassword}
            onChange={(e) => setAppPassword(e.target.value)}
            className="w-full mb-3 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-purple-500"
          />

          <button
            onClick={handleSaveGmail}
            className="w-full py-2 px-4 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg shadow transition-colors duration-200"
          >
            Save Gmail Settings
          </button>

          {message && (
            <p className="text-sm mt-2 text-center text-gray-700 dark:text-gray-300">{message}</p>
          )}

          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            ⚠️ Use your <strong>App Password</strong> (not normal Gmail password). Enable 2FA to create one.
          </p>
        </div>

        {/* --- Logout Button --- */}
        <button
          onClick={handleLogout}
          className="w-full mt-6 py-3 px-4 rounded-lg bg-red-500 hover:bg-red-600 text-white font-bold flex items-center justify-center transition-colors duration-200"
        >
          <LogOut size={20} className="mr-2" />
          Log Out
        </button>
      </div>
    </div>
  );
};

export default UserProfile;
