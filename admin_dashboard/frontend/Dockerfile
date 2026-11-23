FROM node:20-alpine

WORKDIR /app

ARG NEXT_PUBLIC_API_URL=http://localhost:4005
ARG NEXT_PUBLIC_ADMIN_API_KEY=
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_ADMIN_API_KEY=${NEXT_PUBLIC_ADMIN_API_KEY}

# Install exact, audited versions from the lockfile (dev deps are needed for the build)
COPY admin_dashboard/frontend/package.json admin_dashboard/frontend/package-lock.json ./
RUN npm ci

ENV NODE_ENV=production

COPY admin_dashboard/frontend .

RUN npm run build

EXPOSE 3000

# Drop root privileges at runtime (Next writes its cache under .next/)
RUN chown -R node:node /app
USER node

CMD ["npm", "start"]