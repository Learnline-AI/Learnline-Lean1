# Node.js Dockerfile for Voice Chat Application
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY server/package*.json ./server/
COPY client/package*.json ./client/

# Install root dependencies
RUN npm install

# Install server dependencies
WORKDIR /app/server
RUN npm install

# Install client dependencies  
WORKDIR /app/client
RUN npm install

# Copy source code
WORKDIR /app
COPY . .

# Build client
RUN cd client && npm run build

# Build server
RUN cd server && npm run build

# Expose port
EXPOSE 3001

# Start server
WORKDIR /app/server
CMD ["node", "dist/index.js"]