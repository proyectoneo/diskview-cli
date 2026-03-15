# 💾 DiskView CLI

**Disk health analyzer and monitor for Linux with colorful terminal graphics**

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)

DiskView CLI analyzes your disk drives showing free/used space with pie charts, health scores with color indicators, and estimates remaining useful life based on S.M.A.R.T. data.

```
  ____  _     _  __     ___               
 |  _ \(_)___| | _\ \   / (_) _____      __
 | | | | / __| |/ /\ \ / /| |/ _ \ \ /\ / /
 | |_| | \__ \   <  \ V / | |  __/\ V  V / 
 |____/|_|___/_|\_\  \_/  |_|\___| \_/\_/  
                              CLI v1.0.0
```

## 🎨 Features

- **📊 Pie Charts** — Visual free/used space representation in terminal
- **💾 Disk Overview** — All partitions with usage bars
- **🔍 S.M.A.R.T. Analysis** — Temperature, power-on hours, reallocated sectors, wear level
- **⏳ Life Estimate** — Calculates estimated remaining useful life
- **🚦 Health Score** — Color-coded 0-100 score (🟢 healthy / 🟡 warning / 🔴 critical)
- **📈 I/O Statistics** — Read/write operations and throughput
- **🔄 Live Mode** — Auto-refreshing dashboard
- **📋 JSON Export** — Machine-readable output

## 🚀 Installation

```bash
curl -sSL https://raw.githubusercontent.com/proyectoneogroup/diskview-cli/main/install.sh | bash
source ~/.bashrc
```



## 📖 Usage

```bash
diskview                 # Disk health dashboard
diskview --live          # Live monitoring
diskview --live -i 10    # Refresh every 10 seconds
diskview --json          # JSON output
diskview --help          # All options
```

## 📸 Preview

```
╭──────── 💾 All Disks Overview ────────╮
│ Device    Total   Used    Health  Life │
│ /dev/sda  500GB   320GB   🟢 85   ~3y │
│ /dev/sdb  1TB     890GB   🟡 45   ~1y │
╰───────────────────────────────────────╯

╭──── 📊 /dev/sda ──────╮  ╭──── 📊 /dev/sdb ──────╮
│    ██████████████       │  │    ██████████████████  │
│   ████████████████     │  │   ████████████████████ │
│   █████████████████    │  │   ████████████████████ │
│    ██████████████       │  │    ██████████████████  │
│                        │  │                        │
│    ██ Used 64.0%       │  │    ██ Used 89.0%       │
│    ██ Free 36.0%       │  │    ██ Free 11.0%       │
╰────────────────────────╯  ╰────────────────────────╯

  Health: ████████████████████░░░░░░░░░░ 85/100
  Status: 🟢 HEALTHY
  ⏳ Estimated life: ~3 years
```

## 🔧 Requirements

- Python 3.8+
- Linux or macOS

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.
