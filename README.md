# Closetly Backend

A robust, scalable, and secure backend API for a fashion marketplace platform.

## Features

- User authentication & profiles
- Wardrobe item uploads & metadata
- Outfit creation & sharing
- Feed and recommendation logic
- Real-time bidding on clothes
- AI tagging & visual similarity search
- Notifications & moderation

## Tech Stack

- **API Framework**: Flask
- **Database**: PostgreSQL
- **Storage**: AWS S3
- **Search**: Meilisearch
- **AI Layer**: OpenAI CLIP + FAISS
- **Background Jobs**: Celery + Redis
- **Auth**: JWT / OAuth2
- **Notifications**: Firebase / OneSignal
- **Real-Time**: WebSocket (Socket.IO)
- **Deployment**: Docker

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- AWS Account (for S3)
- Firebase/OneSignal Account (for notifications)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Flask
SECRET_KEY=your-secret-key
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/fitcheck

# JWT
JWT_SECRET_KEY=your-jwt-secret

# AWS
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1

# Redis
REDIS_URL=redis://redis:6379/0

# Meilisearch
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_MASTER_KEY=masterKey

# Firebase/OneSignal
FIREBASE_CREDENTIALS={"type": "service_account", ...}
ONESIGNAL_APP_ID=your-app-id
ONESIGNAL_API_KEY=your-api-key

# Security
PASSWORD_SALT=your-salt
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/closetly-backend.git
cd closetly-backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the services using Docker Compose:
```bash
docker-compose up -d
```

5. Run database migrations:
```bash
flask db upgrade
```

## Development

- Run tests:
```bash
pytest
```

- Start the development server:
```bash
flask run
```

- Start Celery worker:
```bash
celery -A app.tasks worker --loglevel=info
```

- Start Celery beat:
```bash
celery -A app.tasks beat --loglevel=info
```

## API Documentation

The API documentation is available at `/docs` when running the server.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 