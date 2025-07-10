import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

const ChatInterface = ({ conversationId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const socket = io('http://localhost:8000');

  useEffect(() => {
    socket.emit('join', conversationId);
    socket.on('message', (message) => {
      setMessages(prev => [...prev, message]);
    });
    return () => socket.disconnect();
  }, [conversationId]);

  const sendMessage = () => {
    if (input.trim()) {
      socket.emit('message', { conversationId, content: input, timestamp: new Date().toISOString() });
      setInput('');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Chat</h1>
      <div className="border p-4 h-96 overflow-y-auto mb-4">
        {messages.map((msg, index) => (
          <div key={index} className="mb-2">
            <span className="text-gray-500">{new Date(msg.timestamp).toLocaleTimeString()}</span>
            <p>{msg.content}</p>
          </div>
        ))}
      </div>
      <div className="flex">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 border p-2 rounded-l"
        />
        <button onClick={sendMessage} className="bg-blue-500 text-white p-2 rounded-r">Send</button>
      </div>
    </div>
  );
};

export default ChatInterface;
