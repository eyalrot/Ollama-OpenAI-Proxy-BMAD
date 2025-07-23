# CI Setup Guide

This guide explains how to set up the CI/CD pipeline for this project.

## Codecov Setup

To avoid rate limiting issues with Codecov, you need to add a Codecov token to your repository:

1. **Get your Codecov token:**
   - Go to [codecov.io](https://codecov.io/)
   - Sign in with your GitHub account
   - Navigate to your repository: `eyalrot/Ollama-OpenAI-Proxy-BMAD`
   - Copy the repository upload token

2. **Add the token to GitHub Secrets:**
   - Go to your GitHub repository
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: Paste your Codecov token
   - Click "Add secret"

## Required Secrets

The following secrets need to be configured in your GitHub repository:

- `OPENAI_API_KEY`: Your OpenAI API key for running integration tests
- `CODECOV_TOKEN`: Your Codecov repository upload token (optional but recommended)

## CI Workflow

The CI workflow (`test.yml`) runs on:
- Push to master, main, or develop branches
- Pull requests to master or main branches

It performs the following steps:
1. Sets up Python 3.12
2. Installs dependencies
3. Starts the proxy server
4. Runs linting (ruff)
5. Runs type checking (mypy)
6. Runs unit tests
7. Runs integration tests (with and without API key)
8. Generates coverage report
9. Uploads coverage to Codecov (if token is configured)

## Troubleshooting

### Codecov Rate Limiting
If you see "Rate limit reached" errors from Codecov, make sure you've added the `CODECOV_TOKEN` secret as described above.

### Integration Test Failures
The integration tests automatically detect if the proxy server is already running (as in CI). If tests fail locally, make sure no other instance of the proxy is running on port 11434.