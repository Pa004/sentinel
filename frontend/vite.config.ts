import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [tailwindcss(), react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/react-dom")) return "vendor"
          if (id.includes("node_modules/react") && !id.includes("react-dom")) return "vendor"
          if (id.includes("node_modules/framer-motion")) return "motion"
        },
      },
    },
  },
})
