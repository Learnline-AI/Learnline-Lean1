# Node.js Dockerfile for Voice Chat Application - v2
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
WORKDIR /app/client
RUN npm run build

# Build server
WORKDIR /app/server
RUN npm run build

# Expose port
EXPOSE 3001

# Start server  
WORKDIR /app/server
ENV NODE_ENV=production
CMD ["node", "dist/index.js"]