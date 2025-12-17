#!/bin/bash

podman-compose down
podman-compose build --no-cache
podman-compose up -d
