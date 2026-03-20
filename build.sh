#!/bin/bash
set -e

echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Copying static files to backend..."
rm -rf backend/static
cp -r frontend/out backend/static

echo "Build complete. The backend is ready to serve the static frontend files."
