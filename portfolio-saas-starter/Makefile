SHELL := /bin/sh

.PHONY: dev dev-api dev-web

dev:
	@echo "Starting API and Web..."
	$(MAKE) -j2 dev-api dev-web

dev-api:
	cd apps/api && npm run dev

dev-web:
	cd apps/web && npm run dev

