# CodeSight Python

A Python utility for collecting and formatting code for LLMs, optimized for performance on M-series Macs.

**Version: 0.1.11**

## Installation

```bash
# Clone the repository
git clone https://github.com/mattsilv/codesight-python.git
cd codesight-python

# Run the installer (installs to /usr/local/bin, /opt/homebrew/bin, or ~/bin)
.codesight/bin/install.sh
```

CodeSight will be installed globally in one of these locations (in order of preference):
- `/usr/local/bin` (if writable)
- `/opt/homebrew/bin` (on Apple Silicon Macs with Homebrew)
- `~/bin` (created if it doesn't exist)

After installation, you can use `cs` from any directory.

## Usage

```bash
# In any project directory:
cs -i                  # Initialize CodeSight in your project
cs                     # Run analysis with standard prompt
cs -b "Bug description" # Run with bug-fixing prompt
cs -t                  # Analyze token usage (show top files by token count)
cs -u                  # Update CodeSight to the latest version
```

For detailed documentation and usage instructions, see [.codesight/README.md](.codesight/README.md).

## License

MIT License - see the [LICENSE](LICENSE) file for details.