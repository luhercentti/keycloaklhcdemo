FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Install Vault client
RUN apt-get update && \
    apt-get install -y curl unzip && \
    curl -L -o vault.zip https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip && \
    unzip vault.zip && \
    mv vault /usr/local/bin/ && \
    rm vault.zip && \
    apt-get remove -y unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add a startup script
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 5000

CMD ["./start.sh"]