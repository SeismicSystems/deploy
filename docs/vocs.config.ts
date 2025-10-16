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
  topNav: [
    {
      text: 'Getting Started',
      items: [
        { text: 'Introduction', link: '/introduction' },
        { text: 'Install', link: '/install' },
      ],
    },
    {
      text: 'Networks',
      items: [
        { text: 'Mainnet', link: '/mainnet' },
        { text: 'Testnet', link: '/testnet' },
      ],
    },
    {
      text: 'Technical',
      items: [
        { text: 'Differences from Ethereum', link: '/ethereum-differences' },
        { text: 'Architecture', link: '/architecture' },
        { text: 'Consensus', link: '/consensus' },
        { text: 'Development Tools', link: '/tools' },
      ],
    },
    {
      text: 'Operations',
      items: [
        { text: 'Node Operators', link: '/node-operator-faq' },
        { text: 'Third-Party', link: '/third-party' },
      ],
    },
    {
      text: 'Legal & Governance',
      items: [
        { text: 'Governance', link: '/governance' },
        { text: 'Compliance', link: '/compliance' },
      ],
    },
    { text: 'Resources', link: '/resources' },
  ],
})

export default config
