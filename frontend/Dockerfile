FROM node:20-alpine

WORKDIR /app

# Install wget für Health Check (Alpine hat kein curl standardmäßig)
RUN apk add --no-cache wget

# Copy package files first (Layer Caching: Dependencies ändern sich seltener als Code)
COPY package*.json ./

# Install dependencies (separate Layer für besseres Caching)
# WICHTIG: npm ci ohne --only=production, da wir builden müssen
RUN npm ci

# Copy source code (separate Layer: Code ändert sich häufiger)
COPY . .

# Build the application (separate Layer)
RUN npm run build

# Expose port
EXPOSE 3000

# Health check (verwendet wget - schneller als Node.js HTTP-Request)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Command to run the application
CMD ["npm", "run", "start"]
