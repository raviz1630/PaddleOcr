# build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY src/ src/
COPY public/ public/
RUN npm run build

# runtime stage
FROM nginx:stable-alpine
COPY --from=builder /app/build /usr/share/nginx/html
# forward logs to Docker
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
