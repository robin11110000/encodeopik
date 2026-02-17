# Frontend Setup (React + Vite)

Follow these steps to install prerequisites, install dependencies, and run the React frontend that lives in this `frontend/` directory.

## 1. Install Node.js (if needed)

1. Check whether Node.js is already available:
   ```bash
   node -v
   npm -v
   ```
2. If either command is missing, install the Long-Term Support (LTS) release of Node.js (which bundles npm):
   - **macOS / Windows**: Download the installer from https://nodejs.org/en/download and run it.
   - **Linux**: Use your package manager (`sudo apt install nodejs npm`, `sudo dnf install nodejs`, etc.) or use `nvm` following the instructions at https://github.com/nvm-sh/nvm.
3. Restart your terminal and re-run `node -v` and `npm -v` to verify the installation.

> Minimum recommended version: **Node.js 18.x** with the npm version that ships alongside it.

### Install Node.js via nvm (alternative method)

If you prefer managing Node.js versions with nvm:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"
nvm install --lts
nvm use --lts
```

Re-open your terminal or source your shell profile after the install so `nvm` is available in every session.

## 2. Install project dependencies

From the `frontend/` directory run:

```bash
npm install
```

This command reads `package.json` and downloads everything into `node_modules/`.

## 3. Run the development server

To start Vite in dev mode with hot module replacement:

```bash
npm run dev
```

- Default URL: http://localhost:5173
- Press `q` or `Ctrl+C` in the terminal to stop the server.

## 4. Build for production

To create an optimized build in `dist/`:

```bash
npm run build
```

To preview that build locally:

```bash
npm run preview
```

## 5. Optional npm scripts

Additional scripts available (if configured in `package.json`):

- `npm run lint` — run ESLint checks
- `npm run test` — execute frontend tests

Refer to `package.json` for the complete list and adjust commands as your workflow evolves.
