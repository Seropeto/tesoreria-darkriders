FROM nginx:alpine

# Copy frontend files to nginx default directory
COPY . /usr/share/nginx/html

# Optional: Add a custom nginx config if we want to handle SPA routing better
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
