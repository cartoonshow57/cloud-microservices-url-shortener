# Microservices URL Shortener with CI/CD on Azure

A cloud-native URL shortener built as two independent microservices, containerized with Docker, orchestrated with Docker Compose, and deployed to an Azure VM with automated CI/CD via GitHub Actions.

## Architecture

```
                         ┌──────────────────────────────────────┐
                         │        GitHub Actions CI/CD          │
                         │   Push → Test → SSH Deploy to VM     │
                         └──────────────┬───────────────────────┘
                                        │
                                        ▼
┌──────────┐      ┌─────────────────────────────────────────────┐
│  Users    │─────▶│          Azure VM (Docker Compose)          │
└──────────┘      │                                             │
                  │   ┌───────────────────────────────────┐     │
                  │   │     Nginx (Reverse Proxy :80)     │     │
                  │   └─────────┬───────────────┬─────────┘     │
                  │             │               │               │
                  │             ▼               ▼               │
                  │   ┌──────────────┐ ┌────────────────┐       │
                  │   │ API Service  │ │Redirect Service│       │
                  │   │ (FastAPI     │ │(FastAPI        │       │
                  │   │  :8001)      │ │ :8002)         │       │
                  │   └──────┬───────┘ └───────┬────────┘       │
                  │          │                 │                │
                  │          ▼                 ▼                │
                  │   ┌─────────────────────────────┐           │
                  │   │      Redis (:6379)           │           │
                  │   └─────────────────────────────┘           │
                  └─────────────────────────────────────────────┘
```

## Tech Stack

| Layer            | Technology                        |
|------------------|-----------------------------------|
| Language         | Python 3.11 + FastAPI             |
| Database         | Redis 7 (Alpine)                  |
| Containerization | Docker + Docker Compose           |
| Reverse Proxy    | Nginx (Alpine)                    |
| Cloud            | Azure Free Tier (B1s Ubuntu VM)   |
| CI/CD            | GitHub Actions                    |

## Project Structure

```
cloud_project/
├── api_service/
│   ├── app.py              # URL shortening API
│   ├── test_app.py         # Unit tests
│   ├── requirements.txt
│   └── Dockerfile
├── redirect_service/
│   ├── app.py              # URL redirect service
│   ├── test_app.py         # Unit tests
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/
│   └── nginx.conf          # Reverse proxy configuration
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD pipeline
├── docker-compose.yml
└── README.md
```

## Microservices

### API Service (Port 8001)

Handles URL shortening — generates a random 6-character code and stores the mapping in Redis.

| Endpoint       | Method | Description                          |
|----------------|--------|--------------------------------------|
| `/shorten`     | POST   | Create a short URL                   |
| `/urls`        | GET    | List all stored URL mappings         |
| `/health`      | GET    | Health check (includes Redis status) |

**Example:**
```bash
# Shorten a URL
curl -X POST http://<VM_IP>/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'

# Response:
# {"short_url":"http://<VM_IP>/abc123","code":"abc123","original_url":"https://www.google.com/"}
```

### Redirect Service (Port 8002)

Resolves short codes and redirects users to the original URL.

| Endpoint       | Method | Description                          |
|----------------|--------|--------------------------------------|
| `/{code}`      | GET    | 307 redirect to original URL         |
| `/health`      | GET    | Health check (includes Redis status) |

**Example:**
```bash
# Follow a short URL (browser will redirect automatically)
curl -L http://<VM_IP>/abc123
```

## Local Development

### Prerequisites

- Docker and Docker Compose installed

### Run Locally

```bash
# Build and start all services
docker compose up -d --build

# Test the API
curl -X POST http://localhost/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'

# Check health
curl http://localhost/api/health
curl http://localhost/redirect/health

# List all URLs
curl http://localhost/urls

# Stop all services
docker compose down
```

### Run Tests

```bash
pip install -r api_service/requirements.txt
pytest api_service/test_app.py -v
pytest redirect_service/test_app.py -v
```

## Azure VM Setup

### Step 1: Create the VM

1. Log in to the [Azure Portal](https://portal.azure.com)
2. Go to **Virtual Machines** → **Create** → **Azure Virtual Machine**
3. Configure:
   - **Subscription**: Free Trial or your subscription
   - **Resource Group**: Create new → `url-shortener-rg`
   - **VM Name**: `url-shortener-vm`
   - **Region**: Choose the closest region to you
   - **Image**: Ubuntu Server 22.04 LTS
   - **Size**: Standard B1s (free tier eligible — 750 hrs/month for 12 months)
   - **Authentication**: SSH public key
   - **Username**: `azureuser`
4. Click **Review + Create** → **Create**
5. Download the SSH private key (.pem file)

### Step 2: Open Port 80

1. Go to your VM → **Networking** → **Network Settings**
2. Click **Create port rule** → **Inbound port rule**
3. Configure:
   - **Destination port**: 80
   - **Protocol**: TCP
   - **Action**: Allow
   - **Name**: `Allow-HTTP`
4. Click **Add**

### Step 3: Install Docker on the VM

```bash
# SSH into the VM
ssh -i <your-key>.pem azureuser@<VM_PUBLIC_IP>

# Install Docker
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow running Docker without sudo
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker run hello-world
```

### Step 4: Deploy the Application

```bash
# On the VM
git clone https://github.com/<YOUR_USERNAME>/cloud_project.git ~/cloud_project
cd ~/cloud_project

# Set the BASE_URL to your VM's public IP
export BASE_URL=http://<VM_PUBLIC_IP>

# Start the application
docker compose up -d --build
```

### Step 5: Configure GitHub Actions Secrets

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add these repository secrets:
   - `AZURE_VM_HOST`: Your VM's public IP address
   - `AZURE_VM_USER`: `azureuser`
   - `AZURE_VM_SSH_KEY`: Contents of your .pem private key file

Now every push to `main` will automatically test and deploy to your Azure VM.

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on every push to `main`:

1. **Test Job**: Spins up a Redis service container, installs dependencies, runs pytest for both services
2. **Deploy Job** (only on main): SSHs into the Azure VM, pulls latest code, rebuilds and restarts containers

```
git push origin main
    │
    ▼
┌─────────┐     ┌──────────┐     ┌─────────────┐
│ Checkout │────▶│ Run Tests│────▶│ SSH Deploy  │
│   Code   │     │ (pytest) │     │ to Azure VM │
└─────────┘     └──────────┘     └─────────────┘
```

## Useful Commands

```bash
# View running containers
docker compose ps

# View logs
docker compose logs -f

# Restart a specific service
docker compose restart api

# Stop everything
docker compose down

# Stop and remove all data
docker compose down -v
```
