// load .env variables
require('dotenv').config();

const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json()); // Allow server to read JSON payloads
app.use(cors());         // Allow frontend to connect to this API

const JWT_SECRET = 'mysecret123'; // Change this in production!
const MONGO_URI = 'mongodb+srv://coder69:db1269@elitecoders.ssdbe7b.mongodb.net/?appName=Elitecoders'; // Connects to local MongoDB

// 1. Connect to MongoDB
mongoose.connect(MONGO_URI, {
  serverSelectionTimeoutMS: 5000,
  tls: true,
  tlsAllowInvalidCertificates: true
})
  .then(() => console.log('✅ Connected to MongoDB Backend!'))
  .catch(err => console.error('MongoDB connection error:', err));

// 2. Define the User Database Schema
const userSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  email: { type: String },
  password: { type: String, required: true }
});
const User = mongoose.model('User', userSchema);

// 2.5. Define the Message Database Schema
const messageSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  chatId: { type: String, required: true },
  role: { type: String, required: true, enum: ['system', 'bot', 'user'] },
  content: { type: String, required: true },
  timestamp: { type: Date, default: Date.now }
});
const Message = mongoose.model('Message', messageSchema);

// Middleware to verify JWT token
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) return res.status(401).json({ message: 'Access denied. No token provided.' });

  try {
    const verified = jwt.verify(token, JWT_SECRET);
    req.user = verified;
    next();
  } catch (error) {
    res.status(403).json({ message: 'Invalid token.' });
  }
};

// 3. API Route: SIGN UP (Register)
app.post('/api/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;

    // Check if user already exists
    const existingUser = await User.findOne({ username });
    if (existingUser) {
      return res.status(400).json({ message: 'Username already taken' });
    }

    // Securely Hash the password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Save exact user to MongoDB
    const newUser = new User({ username, email, password: hashedPassword });
    await newUser.save();

    // Create a login token for the frontend to hold onto
    const token = jwt.sign({ userId: newUser._id }, JWT_SECRET, { expiresIn: '1h' });

    res.status(200).json({ token, user: { username, email } });
  } catch (error) {
    res.status(500).json({ message: 'Server error during registration' });
  }
});

// 4. API Route: SIGN IN (Login)
app.post('/api/login', async (req, res) => {
  try {
    const { username, email, password } = req.body;

    // Find the user by either email or username in MongoDB
    const userToFind = username ? { username } : { email };
    const user = await User.findOne(userToFind);

    if (!user) {
      return res.status(400).json({ message: 'User not found in database' });
    }

    // Compare the submitted password to the hashed DB password
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }

    // If passwords match, grant login session token
    const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '1h' });
    res.status(200).json({ token, user: { username: user.username, email: user.email } });
  } catch (error) {
    res.status(500).json({ message: 'Server error during login' });
  }
});

// 5. API Route: GET /api/chat-sessions (Retrieve list of all chats)
app.get('/api/chat-sessions', authenticateToken, async (req, res) => {
  try {
    const sessions = await Message.aggregate([
      { $match: { userId: new mongoose.Types.ObjectId(req.user.userId) } },
      { $sort: { timestamp: 1 } },
      {
        $group: {
          _id: "$chatId",
          firstMessage: { $first: "$content" },
          lastUpdated: { $max: "$timestamp" }
        }
      },
      { $sort: { lastUpdated: -1 } }
    ]);
    res.status(200).json(sessions);
  } catch (error) {
    res.status(500).json({ message: 'Server error retrieving sessions' });
  }
});

// 6. API Route: GET /api/chats/:chatId (Retrieve History)
app.get('/api/chats/:chatId', authenticateToken, async (req, res) => {
  try {
    const messages = await Message.find({
      userId: req.user.userId,
      chatId: req.params.chatId
    }).sort({ timestamp: 1 });
    res.status(200).json(messages);
  } catch (error) {
    res.status(500).json({ message: 'Server error retrieving messages' });
  }
});

// 7. API Route: POST /api/chats (Save Message)
app.post('/api/chats', authenticateToken, async (req, res) => {
  try {
    const { chatId, role, content } = req.body;

    if (!chatId || !role || !content) {
      return res.status(400).json({ message: 'chatId, role, and content are required' });
    }

    const newMessage = new Message({
      userId: req.user.userId,
      chatId,
      role,
      content
    });

    await newMessage.save();
    res.status(201).json(newMessage);
  } catch (error) {
    res.status(500).json({ message: 'Server error saving message' });
  }
});

// 7. API Route: POST /api/generate (Proxy to Python AI service and persist bot reply)
// This endpoint is intentionally open so the web UI can function without login.
app.post('/api/generate', async (req, res) => {
  try {
    const { chatId, message } = req.body;

    if (!chatId || !message) {
      return res.status(400).json({ message: 'chatId and message are required' });
    }

    // determine userId if token present
    let userId = null;
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    if (token) {
      try {
        const verified = jwt.verify(token, JWT_SECRET);
        userId = verified.userId;
      } catch (e) {
        // ignore invalid token
      }
    }

    // Call local Python AI service
    const pythonRes = await fetch('http://localhost:8000/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    if (!pythonRes.ok) {
      const errText = await pythonRes.text();
      return res.status(502).json({ message: 'AI service error', detail: errText });
    }

    const gen = await pythonRes.json();
    const botContent = gen.reply || 'No reply from AI service';

    // Save bot message to MongoDB if we have a user
    if (userId) {
      const botMessage = new Message({
        userId,
        chatId,
        role: 'bot',
        content: botContent
      });
      await botMessage.save();
    }

    res.status(200).json({ reply: botContent });
  } catch (error) {
    res.status(500).json({ message: 'Server error generating message', error: error.message });
  }
});

// 8. Turn the server on!
const PORT = 5000;
app.listen(PORT, () => console.log(`🚀 API Server running on port ${PORT}`));
