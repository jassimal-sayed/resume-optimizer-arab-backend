#!/bin/bash
set -e

# Update and install basics
echo "Updating apt..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git

# Install Docker
echo "Installing Docker..."
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to docker group (if not root, but usually runs as root on initial setup)
if [ "$USER" != "root" ]; then
    sudo usermod -aG docker "$USER"
    echo "Added $USER to docker group to run without sudo. Log out and back in for changes to take effect."
fi

echo "Docker installation complete!"
docker --version
docker compose version
