# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/devcontainers/python:3.10

# Install minimal OS packages; extend as needed later (e.g., FreeCAD deps).
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/SquatchCut
