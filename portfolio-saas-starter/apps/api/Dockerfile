FROM node:20-alpine AS deps
WORKDIR /usr/src/app
COPY package.json ../../package.json ./

FROM node:20-alpine AS build
WORKDIR /usr/src/app
COPY --from=deps /usr/src/app/package.json package.json
COPY tsconfig.json tsconfig.json
COPY src src
RUN npm i -g typescript && tsc -p tsconfig.json

FROM node:20-alpine AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production
COPY --from=build /usr/src/app/dist dist
EXPOSE 3000
CMD ["node", "dist/index.js"]

