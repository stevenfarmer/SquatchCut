# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/devcontainers/python:3.10

# Install base tooling plus FreeCAD for headless CLI usage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    freecad \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/SquatchCut
