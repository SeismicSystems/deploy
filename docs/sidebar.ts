import type { Sidebar } from 'vocs'

export const sidebar = {
  '/introduction': [
    {
      text: 'Overview',
      collapsed: false,
      items: [
        { text: 'What is Seismic?', link: '/introduction#what-is-seismic-network' },
        { text: 'Key Features', link: '/introduction#key-features' },
        { text: 'Documentation Structure', link: '/introduction#documentation-structure' },
        { text: 'Quick Start', link: '/introduction#quick-start' },
      ],
    },
  ],
  '/install': [
    {
      text: 'Installation',
      collapsed: false,
      items: [
        { text: 'Prerequisites', link: '/install#1-install-prerequisites' },
        { text: 'Download sfoundryup', link: '/install#2-download-sfoundryup' },
        { text: 'Install Tools', link: '/install#3-install-development-tools' },
        { text: 'Clean Projects', link: '/install#4-clean-existing-projects' },
        { text: 'VSCode Extension', link: '/install#vscode-extension' },
      ],
    },
  ],
  '/mainnet': [
    {
      text: 'Mainnet',
      collapsed: false,
      items: [
        { text: 'Network Configuration', link: '/mainnet#network-configuration' },
        { text: 'Genesis Date', link: '/mainnet#genesis-date' },
        { text: 'Gas Pricing', link: '/mainnet#gas-pricing' },
        { text: 'Block Explorer', link: '/mainnet#block-explorer' },
        { text: 'Wrapped Token', link: '/mainnet#wrapped-native-token' },
        { text: 'Network Status', link: '/mainnet#network-status' },
      ],
    },
  ],
  '/testnet': [
    {
      text: 'Testnet',
      collapsed: false,
      items: [
        { text: 'Network Configuration', link: '/testnet#network-configuration' },
        { text: 'Getting Tokens', link: '/testnet#getting-testnet-tokens' },
        { text: 'Wrapped Token', link: '/testnet#wrapped-native-token' },
      ],
    },
  ],
  '/ethereum-differences': [
    {
      text: 'Overview',
      collapsed: false,
      items: [
        { text: 'Introduction', link: '/ethereum-differences#overview' },
      ],
    },
    {
      text: 'EVM Compatibility',
      collapsed: false,
      items: [
        { text: "What's Added", link: '/ethereum-differences#whats-added' },
        { text: "What's Modified", link: '/ethereum-differences#whats-modified' },
        { text: "What's the Same", link: '/ethereum-differences#whats-the-same' },
      ],
    },
    {
      text: 'Transactions',
      collapsed: false,
      items: [
        { text: 'Transaction Types', link: '/ethereum-differences#transaction-types' },
      ],
    },
    {
      text: 'RPC',
      collapsed: false,
      items: [
        { text: 'Modified Methods', link: '/ethereum-differences#modified-methods' },
        { text: 'Supported Methods', link: '/ethereum-differences#supported-methods' },
        { text: 'Configuration', link: '/ethereum-differences#configuration-parameters' },
        { text: 'State Overrides', link: '/ethereum-differences#state-overrides' },
      ],
    },
    {
      text: 'Token Standards',
      collapsed: false,
      items: [
        { text: 'SRC20', link: '/ethereum-differences#src20-token-standard' },
      ],
    },
    {
      text: 'Other',
      collapsed: false,
      items: [
        { text: 'Solidity Compatibility', link: '/ethereum-differences#solidity-compatibility' },
        { text: 'Finality', link: '/ethereum-differences#finality' },
        { text: 'Miscellaneous', link: '/ethereum-differences#other-differences' },
      ],
    },
  ],
  '/architecture': [
    {
      text: 'Overview',
      collapsed: false,
      items: [
        { text: 'What Makes Seismic Unique', link: '/architecture#what-makes-seismic-unique' },
        { text: 'Required Binaries', link: '/architecture#required-binaries' },
      ],
    },
    {
      text: 'Deployment',
      collapsed: false,
      items: [
        { text: 'Deployment Method', link: '/architecture#deployment-method' },
      ],
    },
    {
      text: 'Hardware',
      collapsed: false,
      items: [
        { text: 'Intel TDX Requirement', link: '/architecture#intel-tdx-requirement' },
        { text: 'Recommended Specs', link: '/architecture#recommended-specifications' },
      ],
    },
    {
      text: 'Configuration',
      collapsed: false,
      items: [
        { text: 'Network Architecture', link: '/architecture#network-architecture' },
        { text: 'Data Directory', link: '/architecture#data-directory' },
        { text: 'Host and Port', link: '/architecture#host-and-port' },
      ],
    },
    {
      text: 'Storage',
      collapsed: false,
      items: [
        { text: 'Requirements', link: '/architecture#storage-requirements' },
        { text: 'Monthly Growth', link: '/architecture#monthly-growth' },
        { text: 'Sync Time', link: '/architecture#sync-time' },
        { text: 'Snapshots', link: '/architecture#snapshots' },
      ],
    },
    {
      text: 'Operations',
      collapsed: false,
      items: [
        { text: 'Graceful Shutdown', link: '/architecture#graceful-shutdown' },
        { text: 'Hard Forks', link: '/architecture#hard-forks' },
      ],
    },
    {
      text: 'Technical Details',
      collapsed: false,
      items: [
        { text: 'Seismic REVM', link: '/architecture#seismic-revm' },
        { text: 'Performance', link: '/architecture#performance' },
        { text: 'Shielded Features', link: '/architecture#shielded-features' },
      ],
    },
  ],
  '/consensus': [
    {
      text: 'Consensus',
      collapsed: false,
      items: [
        { text: 'Summit Client', link: '/consensus#summit-consensus-client' },
        { text: 'Simplex Algorithm', link: '/consensus#simplex-consensus-algorithm' },
        { text: 'Finality', link: '/consensus#finality' },
        { text: 'Block Production', link: '/consensus#block-production' },
        { text: 'Finality Tags', link: '/consensus#finality-tags' },
        { text: 'Node Participation', link: '/consensus#node-participation' },
      ],
    },
  ],
  '/tools': [
    {
      text: 'Development Tools',
      collapsed: false,
      items: [
        { text: 'Seismic Solidity', link: '/tools#seismic-solidity' },
        { text: 'Seismic Forge', link: '/tools#seismic-forge-sforge' },
        { text: 'Sanvil', link: '/tools#sanvil' },
        { text: 'Seismic Compiler', link: '/tools#seismic-compiler-ssolc' },
      ],
    },
  ],
  '/third-party': [
    {
      text: 'Third-Party Infrastructure',
      collapsed: false,
      items: [
        { text: 'Bridges', link: '/third-party#bridges' },
        { text: 'Oracles', link: '/third-party#oracles' },
        { text: 'RPC Providers', link: '/third-party#rpc-providers' },
        { text: 'Custody Solutions', link: '/third-party#custody-solutions' },
      ],
    },
  ],
  '/resources': [
    {
      text: 'Resources & Contact',
      collapsed: false,
      items: [
        { text: 'Documentation Sites', link: '/resources#documentation-sites' },
        { text: 'GitHub Repositories', link: '/resources#github-repositories' },
        { text: 'Community', link: '/resources#community-support' },
        { text: 'Contact', link: '/resources#contact' },
        { text: 'Communication', link: '/resources#communication-channels' },
      ],
    },
  ],
  '/node-operator-faq': [
    {
      text: 'Node Operator FAQ',
      collapsed: false,
      items: [
        { text: 'RPC Operations', link: '/node-operator-faq#rpc-operations' },
        { text: 'Storage & Performance', link: '/node-operator-faq#storage-performance' },
        { text: 'Operations', link: '/node-operator-faq#operations' },
      ],
    },
  ],
  '/governance': [
    {
      text: 'Network Participation',
      collapsed: false,
      items: [
        { text: 'Staking', link: '/governance#staking' },
        { text: 'Governance', link: '/governance#governance' },
        { text: 'Actions at Launch', link: '/governance#actions-at-network-launch' },
        { text: 'Vesting', link: '/governance#vesting-schedules' },
      ],
    },
    {
      text: 'Tokenomics',
      collapsed: false,
      items: [
        { text: 'Token Supply', link: '/governance#total-token-supply' },
        { text: 'FDV', link: '/governance#fully-diluted-value-fdv' },
        { text: 'Investors', link: '/governance#institutional-investors' },
        { text: 'Reserve', link: '/governance#foundation-reserve' },
        { text: 'TGE', link: '/governance#token-generation-event-tge' },
      ],
    },
  ],
  '/compliance': [
    {
      text: 'Token Classification',
      collapsed: false,
      items: [
        { text: 'Is Token a Security?', link: '/compliance#is-the-seismic-token-a-security' },
      ],
    },
    {
      text: 'Entity Information',
      collapsed: false,
      items: [
        { text: 'Entity Domicile', link: '/compliance#entity-domicile' },
        { text: 'Team Location', link: '/compliance#team-location' },
      ],
    },
    {
      text: 'Compliance Programs',
      collapsed: false,
      items: [
        { text: 'AML Program', link: '/compliance#anti-money-laundering-aml-program' },
        { text: 'NY Customers', link: '/compliance#new-york-customers' },
      ],
    },
    {
      text: 'Other',
      collapsed: false,
      items: [
        { text: 'USD Custody', link: '/compliance#usd-custody' },
      ],
    },
  ],
  '/': [
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
        { text: 'Node Operator FAQ', link: '/node-operator-faq' },
        { text: 'Third-Party Infrastructure', link: '/third-party' },
      ],
    },
    {
      text: 'Legal & Governance',
      items: [
        { text: 'Governance', link: '/governance' },
        { text: 'Compliance', link: '/compliance' },
      ],
    },
    {
      text: 'Support',
      items: [
        { text: 'Resources & Contact', link: '/resources' },
      ],
    },
  ],
} as const satisfies Sidebar
