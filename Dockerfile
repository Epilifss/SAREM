# Etapa 1: Build da aplicação Node
FROM node:20-alpine AS build

WORKDIR /app

# Copiar arquivos de dependências
COPY package.json package-lock.json ./

# Instalar dependências
RUN npm install

# Copiar todo o código do projeto
COPY . .

# Construir o bundle de produção
RUN npm run build

# Etapa 2: Servir com Nginx
FROM nginx:alpine

# Copiar configuração personalizada do Nginx para suportar React Router (SPA)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar os arquivos compilados da etapa de build
COPY --from=build /app/dist /usr/share/nginx/html

# Expor porta 80
EXPOSE 80

# Iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"]
