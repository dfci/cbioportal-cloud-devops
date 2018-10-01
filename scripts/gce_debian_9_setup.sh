#!/usr/bin/env bash

# Install Docker
apt-get update
apt-get install -y software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
apt-get update
apt-get install -y docker-ce

# Install Docker Compose
curl -L \
    "https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create EXT4 Filesystem on /dev/sdb
mkfs.ext4 /dev/sdb

# Add /dev/sdb to fstab
echo "/dev/sdb  /root/cbioportal-cloud-devops/mountpoints/cbioportal-mysql-data ext4 defaults 1 1" >> /etc/fstab
# Mount /dev/sdb
mount /dev/sdb