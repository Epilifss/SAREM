# Etapa 1: Build da aplicação Node
FROM node:20-alpine AS build

WORKDIR /app

# Declarar ARGs de build (passados via docker-compose ou --build-arg)
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

# Tornar disponíveis como variáveis de ambiente para o Vite
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

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

# Copiar template do Nginx. A imagem oficial substitui PROTHEUS_API_KEY ao iniciar.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Copiar os arquivos compilados da etapa de build
COPY --from=build /app/dist /usr/share/nginx/html

# Expor porta 80
EXPOSE 80

# Iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"]
