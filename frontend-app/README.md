
-----

# 🤖 Personal AI Chat Assistant

**Personal AI** is a full-stack web application that offers a real-time, interactive chat experience powered by the Gemini AI API. It allows users to create, manage, and revisit multiple chat threads, with all conversational data securely stored in a MongoDB database. The application is designed to be a personal, intelligent assistant, providing a seamless and responsive user interface.

\<br\>

\<div align="center"\>

\</div\>

-----

## ✨ Key Features

  - **Real-Time AI Chat:** Engage in dynamic conversations with an AI assistant.
  - **Thread Management:** Create new chat threads, switch between existing ones, and delete conversations you no longer need.
  - **Persistent Chat History:** All messages are saved to a **MongoDB** database, allowing you to easily resume past conversations.
  - **Responsive UI:** A clean, modern, and user-friendly interface that works on both desktop and mobile devices.
  - **Live Deployment:** The application is fully deployed and accessible on the web, with separate services for the frontend and backend.

-----

## 🚀 Live Application & Repository

| Service | Status | URL |
| :--- | :--- | :--- |
| **Frontend** | Deployed | [https://personal-ai-frontend.onrender.com](https://personal-ai-frontend.onrender.com) |
| **Backend** | Deployed | [https://personal-ai-jbvf.onrender.com](https://personal-ai-jbvf.onrender.com) |
| **Repository** | Active | [https://github.com/ASHRITHGOUD/Personal-AI](https://github.com/ASHRITHGOUD/Personal-AI) |

-----

## ⚙️ System Architecture

```plaintext
Frontend (React) <---> Backend (Node.js/Express) <---> Gemini API (AI)
      ^                             |
      |                             |
      |                             |
      |-----------------------------|
           MongoDB (Database)
```

-----

## 📦 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React, Vite, CSS |
| **Backend** | Node.js, Express.js |
| **Database** | MongoDB Atlas, Mongoose |
| **AI Integration** | Gemini API |
| **Deployment** | Render.com |

-----

## 🛠️ Installation & Setup

To get a local copy of this project up and running, follow these steps:

### 1\. Clone the repository

```bash
git clone https://github.com/ASHRITHGOUD/Personal-AI.git
cd Personal-AI
```

### 2\. Backend Setup

Navigate to the `Backend` directory, install dependencies, and configure your environment variables.

```bash
cd Backend
npm install
```

Create a `.env` file in the `Backend` directory and add the following keys with your credentials:

```
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_gemini_api_key
```

Start the backend server:

```bash
npm start
```

### 3\. Frontend Setup

Open a new terminal, navigate to the `Frontend` directory, and install dependencies.

```bash
cd ../Frontend
npm install
```

Create a `.env.local` file in the `Frontend` directory to configure the backend API URL:

```
VITE_API_URL=http://localhost:8000
```

Start the frontend development server:

```bash
npm run dev
```

The application should now be accessible at `http://localhost:5173`.

-----

## 📩 Contact

If you have any questions or suggestions, feel free to reach out\!

  * **Email:** jinukuntlaashrithgoud777@gmail.com
  * **GitHub:** [ASHRITHGOUD](https://www.google.com/search?q=https://github.com/ASHRITHGOUD)

-----

> **Personal AI** — Your intelligent companion, always ready to chat.


Contribution: Added by Kruthin
