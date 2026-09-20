import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { JoinCreateChat } from '../components/JoinCreateChat';
import { ChatPage } from '../components/ChatPage';
import { App } from '../App';

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<JoinCreateChat />} />
      <Route path="/join" element={<JoinCreateChat />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/starter" element={<App />} />
    </Routes>
  );
};

export default AppRoutes;
