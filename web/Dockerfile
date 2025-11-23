# multi-stage dockerfile for react web interface

# development stage
FROM node:20-alpine AS development
WORKDIR /app

# copy package files
COPY package*.json ./

# install dependencies
RUN npm ci

# copy source code
COPY . .

# expose vite dev server port
EXPOSE 3000

# start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# build stage
FROM node:20-alpine AS build
WORKDIR /app

# copy package files
COPY package*.json ./

# install dependencies
RUN npm ci

# copy source code
COPY . .

# build for production
RUN npm run build

# production stage
FROM nginx:alpine AS production
WORKDIR /usr/share/nginx/html

# remove default nginx static files
RUN rm -rf ./*

# copy built assets from build stage
COPY --from=build /app/dist .

# copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# expose port
EXPOSE 80

# start nginx
CMD ["nginx", "-g", "daemon off;"]
