import { defineConfig } from 'vocs'
import type { Config } from 'vocs'

// eslint-disable-next-line no-relative-import-paths/no-relative-import-paths
import { sidebar } from './sidebar.ts'

const config: Config = defineConfig({
  title: 'Seismic Node Docs',
  description: 'Documentation for running nodes and integrating with the Seismic Network',
  iconUrl: '/favicon.ico',
  theme: {
    accentColor: {
      light: '#ff9318',
      dark: '#ffc517',
    },
  },
  rootDir: '.',
  sidebar,
  socials: [
    {
      icon: 'github',
      link: 'https://github.com/SeismicSystems',
    },
    {
      icon: 'discord',
      link: 'https://discord.gg/MnMJ37JN',
    },
    {
      icon: 'x',
      link: 'https://x.com/SeismicSys',
    },
  ],
})

export default config
