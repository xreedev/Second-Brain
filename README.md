<div align="center">

<br/>

```
███████╗███████╗ ██████╗ ██████╗ ███╗   ██╗██████╗     ██████╗ ██████╗  █████╗ ██╗███╗   ██╗
██╔════╝██╔════╝██╔════╝██╔═══██╗████╗  ██║██╔══██╗    ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║
███████╗█████╗  ██║     ██║   ██║██╔██╗ ██║██║  ██║    ██████╔╝██████╔╝███████║██║██╔██╗ ██║
╚════██║██╔══╝  ██║     ██║   ██║██║╚██╗██║██║  ██║    ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║
███████║███████╗╚██████╗╚██████╔╝██║ ╚████║██████╔╝    ██████╔╝██║  ██║██║  ██║██║██║ ╚████║
╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
```

### *Your personal knowledge hub — capture, connect, and recall ideas effortlessly.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![CSS3](https://img.shields.io/badge/CSS3-Styled-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge)]()

<br/>

[**Live Demo**](#) · [**Report Bug**](https://github.com/xreedev/Second-Brain/issues) · [**Request Feature**](https://github.com/xreedev/Second-Brain/issues)

<br/>

</div>

---

## 🧠 What is Second Brain?

**Second Brain** is a full-stack web application that serves as your personal, persistent knowledge management system. Inspired by the *Building a Second Brain* methodology, this app lets you offload mental overhead by capturing notes, bookmarks, and ideas — then resurface them exactly when you need them.

> *"Your mind is for having ideas, not holding them."* — David Allen

Whether you're a student, developer, or researcher, Second Brain gives you a structured space to **store** what you know, **connect** related ideas, and **retrieve** information without digging through browser tabs or scattered notes.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📝 **Content Capture** | Save notes, URLs, and ideas with a single click |
| 🏷️ **Tagging System** | Organize entries with flexible, multi-tag categorization |
| 🔍 **Instant Search** | Find anything across your knowledge base in milliseconds |
| 🔗 **Link Sharing** | Share a curated view of your brain with a unique public link |
| 🔐 **Secure Auth** | JWT-based authentication to keep your data private |
| 📱 **Responsive UI** | Seamlessly works on desktop and mobile browsers |
| ⚡ **REST API** | Clean, documented API backend for easy extensibility |

---

## 🏗️ Architecture

```
second-brain/
├── backend/                  # Python REST API server
│   ├── app.py                # Application entry point
│   ├── models/               # Data models & schemas
│   ├── routes/               # API route handlers
│   ├── auth/                 # Authentication middleware
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # Client-side application
│   ├── index.html            # Entry HTML
│   ├── src/
│   │   ├── app.js            # Main application logic
│   │   ├── api.js            # API communication layer
│   │   └── components/       # Reusable UI components
│   └── styles/
│       └── main.css          # Application styles
│
└── .gitignore
```

---

## 🛠️ Tech Stack

### Backend
- **Python** — Core language powering the server-side logic
- **REST API** — Clean, resource-based HTTP endpoints
- **JWT Authentication** — Stateless, secure token-based auth

### Frontend
- **Vanilla JavaScript (ES6+)** — Lightweight, dependency-free client
- **CSS3** — Custom responsive styling with modern layout techniques
- **HTML5** — Semantic, accessible markup

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js (optional, for any build tooling)
- A modern web browser

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/xreedev/Second-Brain.git
cd Second-Brain
```

**2. Set up the backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment variables**

```bash
cp .env.example .env
# Edit .env and fill in your values:
# SECRET_KEY=your_secret_key
# DATABASE_URL=your_database_url
# JWT_EXPIRY=3600
```

**4. Start the backend server**

```bash
python app.py
# Server runs at http://localhost:5000
```

**5. Launch the frontend**

```bash
cd ../frontend
# Open index.html in your browser, or serve it:
python -m http.server 3000
# Visit http://localhost:3000
```

---

## 📡 API Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|:---:|
| `POST` | `/api/auth/register` | Create a new account | ❌ |
| `POST` | `/api/auth/login` | Authenticate and get JWT | ❌ |
| `GET` | `/api/content` | Fetch all saved content | ✅ |
| `POST` | `/api/content` | Add new content | ✅ |
| `DELETE` | `/api/content/:id` | Remove a content item | ✅ |
| `GET` | `/api/brain/share` | Get public share link | ✅ |

---

## 📸 Screenshots

> *Screenshots coming soon — deploy and update with your live demo.*

---

## 🤝 Contributing

Contributions are welcome and appreciated! Here's how to get involved:

```bash
# 1. Fork the repository
# 2. Create your feature branch
git checkout -b feature/AmazingFeature

# 3. Commit your changes
git commit -m 'Add AmazingFeature'

# 4. Push to the branch
git push origin feature/AmazingFeature

# 5. Open a Pull Request
```

Please make sure your code follows the existing style and includes relevant comments.

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

---

## 👤 Author

**Sreedev** ([@xreedev](https://github.com/xreedev))

> *Building tools that make thinking easier.*

<div align="center">

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-xreedev-181717?style=for-the-badge&logo=github)](https://github.com/xreedev)

<br/>

*If this project helped you, consider giving it a* ⭐

</div>
