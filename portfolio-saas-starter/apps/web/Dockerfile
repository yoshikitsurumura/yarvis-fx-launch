FROM node:20-alpine AS deps
WORKDIR /usr/src/app
COPY package.json ../../package.json ./

FROM node:20-alpine AS build
WORKDIR /usr/src/app
COPY --from=deps /usr/src/app/package.json package.json
COPY tsconfig.json tsconfig.json
COPY vite.config.ts vite.config.ts
COPY index.html index.html
COPY src src
RUN npm i -g vite typescript && vite build

FROM node:20-alpine AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production
RUN npm i -g serve
COPY --from=build /usr/src/app/dist dist
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]

