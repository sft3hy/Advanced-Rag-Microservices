# Use an official Node runtime as a parent image
FROM node:20-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port Vite runs on
EXPOSE 5173

# Start the development server
# Note: The actual command is overridden in docker-compose.yml 
# to ensure the host binding works (npm run dev -- --host)
CMD ["npm", "run", "dev", "--", "--host"]