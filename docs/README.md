# Seismic Network Documentation

This directory contains comprehensive documentation for integrating with and operating on the Seismic Network. The documentation is built using [Vocs](https://vocs.dev/) and provides organized, searchable guides for developers, node operators, and institutional partners.

## Documentation Structure

The documentation is organized into the following sections:

### Getting Started
- **[Introduction](./pages/introduction.mdx)** - Overview of Seismic, key features, and documentation structure
- **[Installation](./pages/install.mdx)** - Set up sforge, sanvil, and ssolc for local development

### Networks
- **[Mainnet](./pages/mainnet.mdx)** - Mainnet configuration, gas pricing, and network status
- **[Testnet](./pages/testnet.mdx)** - Testnet endpoints, faucet information, and testing resources

### Technical Documentation
- **[Differences from Ethereum](./pages/ethereum-differences.mdx)** - EVM enhancements, RPC modifications, SRC20 tokens, and transaction types
- **[Architecture](./pages/architecture.mdx)** - Node architecture, Intel TDX requirements, hardware specs, and storage
- **[Consensus](./pages/consensus.mdx)** - Summit consensus client, Simplex algorithm, and finality
- **[Development Tools](./pages/tools.mdx)** - Seismic Solidity, sforge, sanvil, and ssolc

### Operations
- **[Node Operator FAQ](./pages/node-operator-faq.mdx)** - RPC operations, storage, performance, and maintenance
- **[Third-Party Infrastructure](./pages/third-party.mdx)** - Bridges, oracles, RPC providers, and custody solutions

### Legal & Governance
- **[Governance](./pages/governance.mdx)** - Staking, governance mechanisms, vesting, and tokenomics
- **[Compliance](./pages/compliance.mdx)** - Regulatory information and compliance considerations

### Support
- **[Resources & Contact](./pages/resources.mdx)** - Documentation sites, GitHub repositories, community links, and contact information

## Development

### Running Locally

```bash
npm install
npm run dev
```

The documentation will be available at `http://localhost:5173` (or another port if 5173 is in use).

### Building for Production

```bash
npm run build
```

### Configuration

- **[vocs.config.ts](./vocs.config.ts)** - Main Vocs configuration including theme, title, and social links
- **[sidebar.ts](./sidebar.ts)** - Sidebar navigation structure with organized sections

## Features

- Structured sections with anchored headings for easy linking
- Code blocks with syntax highlighting
- Tables for quick reference
- Cross-references between related topics
- Organized sidebar navigation with collapsible sections
- Search functionality (provided by Vocs)
- Mobile-responsive design

## Contact

For questions not covered in these docs:
- **Email**: c@seismic.systems
- **Website**: https://seismic.systems
- **Documentation**: https://docs.seismic.systems
- **Status Page**: https://status.seismicdev.net
- **Discord**: https://discord.gg/MnMJ37JN
- **Twitter**: [@SeismicSys](https://x.com/SeismicSys)
