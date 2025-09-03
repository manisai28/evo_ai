import React from 'react';
import { Settings, LogOut, ArrowLeft } from 'lucide-react';

const UserProfile = ({ onClose }) => {
  const user = {
    name: 'ASH',
    email: 'ash@personalai.com',
    avatar: '/ms.jpg',
  };

  const handleLogout = () => {
    alert('Logging out...');
    window.location.reload(); 
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

        <div className="flex flex-col items-center mt-4 mb-6">
          <img
            src={user.avatar}
            alt="User Avatar"
            className="w-24 h-24 rounded-full border-4 border-purple-500 shadow-md"
          />
          <h3 className="mt-4 text-2xl font-bold dark:text-white">{user.name}</h3>
          <p className="text-gray-500 dark:text-gray-400">{user.email}</p>
        </div>

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