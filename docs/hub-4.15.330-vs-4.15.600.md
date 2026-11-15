# Harmony Hub (`Skin 97` / `106`) Firmware Changelog: `4.15.330` vs. `4.15.600`

Logitech superseded Harmony Hub firmware **`4.15.330`** (`2023-03-09`) on its public SUS servers when **`4.15.600`** (`4.15.600.2987731.hfw2`, built `2025-08-12`) was published.

By comparing read-only `mtd1` (`uImage`) and `mtd3` (`harmony-image.squashfs`) partition dumps from a stock Harmony Hub running `4.15.330` against the official `4.15.600.2987731.hfw2` bundle, this document records the verification hashes for `4.15.330` and the complete file-level changelog between the two releases.

> **Note:** No firmware binaries are distributed here—only cryptographic digests, header metadata, and clean-room changelog notes.

---

## 1. Summary of Changes (`4.15.330` → `4.15.600`)

Despite a two-and-a-half-year gap (**March 9, 2023 → August 12, 2025**, three months *after* Logitech's May 2025 legacy USB remote server shutdown), **`4.15.600` is a targeted TLS & dead-integration maintenance update**:

1. **TLS Stack Replaced (`axTLS` → `wolfSSL` with TLS 1.2 & TLS 1.3 + 18-CA Root Bundle):**
   - In `4.15.330`, `/opt/lib/luaworks.so.0.0.0` (`279,712 B`) statically embedded the legacy **`axTLS`** library (`socket.axtls`), which lacked modern TLS 1.2/1.3 cipher suite and Root CA support.
   - In `4.15.600`, Logitech replaced `axTLS` inside `/opt/lib/luaworks.so.0.0.0` (`582,272 B`, `+302.5 KB`) with **`wolfSSL`** (`socket.wolfssl`, supporting `TLSv1.2` and `TLSv1.3`) and added **`/opt/luaworks/cacert.pem`** (`25,995 B`, 18 Root CAs including Amazon Root CA 1/2, DigiCert G2/G3/G4, Google Trust Services `GTS Root R1`, GlobalSign, and GoDaddy/Starfield).
2. **RTC-Less Boot Clock vs. Certificate Validation Fix:**
   - Because Harmony Hub lacks a battery-backed real-time clock (RTC), it boots prior to NTP/HTTP time sync with a pre-current date—which would cause strict `wolfSSL` certificate expiration validation to fail before reaching cloud discovery/time endpoints.
   - `rcmgr.lua`, `discovery.lua`, `timemanager.lua`, `netservicestarter.lua`, and `cloudapi.lua` were updated to inspect `os.date("%Y")`, defer certificate date enforcement prior to time sync (`"Skipping certificate validation (due to time) for URL:"`), and fetch UTC time via `GET` (`TimeServer/current` / `/time/current`) immediately after `/Discovery.svc`.
3. **Sonos Local WebSocket TLS Updated (`sonosws.lua`):**
   - Migrated Sonos local `wss://` client sockets from `sslcontext` (`axTLS`) to `sslcontextclient` (`wolfSSL`).
4. **Belkin WeMo & DISH Hopper Plugins Removed (`653` → `652` SquashFS Inodes):**
   - Removed `/opt/luaworks/tasks/automation/plugins/wemo.lua` (`24,438 B` — Belkin WeMo smart plug local UPnP integration).
   - Removed `/opt/luaworks/tasks/harmonyengine/plugins/hopper.lua` (`20,595 B` — DISH Network / EchoStar Hopper & Joey DVR plugin) and stripped `Belkin`/`WeMo` and `Echostar`/`Hopper`/`Joey` UPnP/SOAP discovery handlers (`-4,495 B`) from `ssdp.lua`, `activity.lua`, and `ipmanager.lua`.
5. **Unchanged Kernel, Base OS, Boot Scripts, Local APIs, and RF:**
   - **Linux Kernel (`2.6.31-g89d565c`):** Identical uncompressed size (`2,671,104 B`). Only `274` bytes differ across the entire uncompressed kernel image (solely the compile timestamp string and embedded initramfs `cpio` `mtime` fields).
   - **Base OS (`/bin`, `/sbin`, `/lib`, `/usr`, `/etc/init.d/*`):** **Zero changes.** Local WebSocket (`:8088`), local XMPP (`:5222`), USB HID provisioning, `/etc/init.d/rcS` boot sequence, and 2.4 GHz RF communication with paired remotes are identical between `4.15.330` and `4.15.600`.

---

## 2. Image & Header Reference Hashes

| Component / Field | `4.15.330` (Hardware `mtd1` / `mtd3`) | `4.15.600` (`4.15.600.2987731.hfw2`) |
| :--- | :--- | :--- |
| **`/etc/version`** | `4.15.330` | `4.15.600` |
| **`/etc/timestamp`** | `030907482023` | `081219282025` |
| **`uImage.bin` Size** | `951,045 B` (`64 B` hdr + `950,981 B` LZMA) | `951,019 B` (`64 B` hdr + `950,955 B` LZMA) |
| **`uImage.bin` SHA-256** | `8cd49e9eb84c9e6b7417652d0935972bf7b1cbd8f6acb6eba2cac397f6f4d34b` | `4cd0f6d3933a45083e6a9416530262cdd4e33f1be84ea27eaeb0b5a7400ce658` |
| **`uImage` Timestamp (UTC)** | `2023-03-09T02:12:10Z` | `2025-08-12T13:54:22Z` |
| **Kernel Banner** | `Linux version 2.6.31-g89d565c ... Thu Mar 9 07:40:24 IST 2023` | `Linux version 2.6.31-g89d565c ... Tue Aug 12 19:23:51 IST 2025` |
| **`harmony-image.squashfs` Size (4K-padded)** | `3,645,440 B` (`bytes_used = 3,641,456 B`) | `3,751,936 B` (`bytes_used = 3,751,725 B`) |
| **`harmony-image.squashfs` SHA-256 (4K-padded)** | `0d2463c0bca9c25de29fa78b3f3e3a42170027de1f35061fb4deb5d9264cbbe8` | `08bdbae4e4aad9d5a21b61b6ce19e5f717428a465c6dbc7342637037e676b213` |
| **SquashFS `mkfs_time` (UTC)** | `2023-03-09T02:18:44Z` | `2025-08-12T13:58:22Z` |
| **SquashFS Format** | SquashFS 4.0 LE, `128 KiB` blocks, `comp=2` (5-byte-header LZMA1, `lc=1, lp=2, pb=2, dict=16 MiB`) | SquashFS 4.0 LE, `128 KiB` blocks, `comp=2` (5-byte-header LZMA1, `lc=1, lp=2, pb=2, dict=16 MiB`) |
| **SquashFS Inode Count** | `653` | `652` |
| **Yocto `luaworks` Recipe** | `luaworks-git-r10` | `luaworks-git-r15` |

*(Technical note on SquashFS unpacking: Pimento SquashFS 4.0 images use OpenWrt/Atheros legacy LZMA1 (`compression_id = 2`) with a 5-byte `props + dict_size` header and no 8-byte uncompressed size field, which can be decompressed directly with Python's `lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA1, ...}])`.)*

---

## 3. Complete Root Filesystem Diff (`653` → `652` Inodes)

- **462 entries** are byte-for-byte identical (`SHA-256` match), including **100%** of `/bin`, `/sbin`, `/lib`, `/usr`, and `/etc/init.d`.
- **167 Lua 5.1 bytecode files (`.lua`)** differ by `+1` byte solely in their embedded Yocto build-path debug header (`-r9` / `luaworks-git-r10` → `-r10` / `luaworks-git-r15`); their compiled instructions and constants are identical.
- **25 files** contain actual content differences (**1 added, 2 removed, 5 binary/version files updated, and 17 Lua modules modified**):

### Added (1)
| Path | Size | Description |
| :--- | ---: | :--- |
| `/opt/luaworks/cacert.pem` | `25,995 B` | 18 PEM Root CAs for `wolfSSL` client validation (Amazon Root CA 1 & 2, GlobalSign Root CA & R3, Baltimore CyberTrust Root, GoDaddy Class 2 & G2, Starfield Class 2 / G2 / Services G2, DigiCert Global Root CA / High Assurance EV / Assured ID G2 & G3 / Global Root G2 & G3 / Trusted Root G4, and Google Trust Services `GTS Root R1`). |

### Removed (2)
| Path | `4.15.330` Size | Description |
| :--- | ---: | :--- |
| `/opt/luaworks/tasks/automation/plugins/wemo.lua` | `24,438 B` | Belkin WeMo smart plug local UPnP automation plugin. |
| `/opt/luaworks/tasks/harmonyengine/plugins/hopper.lua` | `20,595 B` | DISH Network / EchoStar Hopper & Joey networked DVR plugin. |

### Modified Binaries & Version Metadata (5)
| Path | `4.15.330` | `4.15.600` | Summary |
| :--- | ---: | ---: | :--- |
| `/etc/version` | `9 B` | `9 B` | `4.15.330` → `4.15.600` |
| `/etc/timestamp` | `13 B` | `13 B` | `030907482023` → `081219282025` |
| `/opt/lib/luaworks.so.0.0.0` | `279,712 B` | `582,272 B` | Replaced statically linked `axTLS` with `wolfSSL` (`TLSv1.2`/`TLSv1.3`, `/opt/luaworks/cacert.pem` loader, `socket.wolfssl` bindings). |
| `/opt/libexec/luaworksdns` | `4,864 B` | `4,864 B` | Recompiled async DNS helper (`luaworks-git-r15`). |
| `/opt/libexec/.debug/luaworksdns` | `8,975 B` | `8,975 B` | Matching debug metadata for `luaworksdns`. |

### Modified Lua 5.1 Modules (17)
| Path | `4.15.330` | `4.15.600` | Delta | Functional Change |
| :--- | ---: | ---: | ---: | :--- |
| `/opt/luaworks/works/ssl.lua` | `2,537 B` | `2,469 B` | `-68 B` | Switched backend from `socket.axtls` to `socket.wolfssl`; disabled unused server SSL context (`deny_works_ssl_server`). |
| `/opt/luaworks/works/socket.lua` | `16,992 B` | `16,631 B` | `-361 B` | Replaced `axtls` handshake/CN checks with `wolfssl` `sslcontextclient` + `shouldValidateCertificate`. |
| `/opt/luaworks/works/http.lua` | `5,261 B` | `5,921 B` | `+660 B` | Integrated `rcmgr` (`isBasicSocket`, `sslcontextclient`) into HTTPS client requests. |
| `/opt/luaworks/works/system.lua` | `57,010 B` | `56,902 B` | `-108 B` | Minor diagnostic `extraInfo` logging adjustment. |
| `/opt/luaworks/tasks/connectserver/core/rcmgr.lua` | `1,260 B` | `4,700 B` | `+3,440 B` | Rewritten Root Certificate Manager (`shouldValidateCertificate`, URL allowlists, pre-time-sync `os.date("%Y")` bypass). |
| `/opt/luaworks/tasks/connectserver/core/policymgr.lua` | `20,336 B` | `20,275 B` | `-61 B` | Removed legacy `signature` policy check. |
| `/opt/luaworks/tasks/connectserver/core/verifiers.lua` | `27,947 B` | `27,925 B` | `-22 B` | Minor verifier bytecode adjustment. |
| `/opt/luaworks/tasks/connectserver/netservicestarter.lua` | `8,209 B` | `8,463 B` | `+254 B` | Added `os.date("%Y")` / `blockingSleep` boot-time clock wait. |
| `/opt/luaworks/tasks/connectserver/transport/cloudapi.lua` | `6,828 B` | `7,035 B` | `+207 B` | Added `os.date("%Y")` year check on cloud transport startup. |
| `/opt/luaworks/tasks/harmonywebservices/proxy/discovery.lua` | `9,976 B` | `12,046 B` | `+2,070 B` | Queries `TimeServer/current` after discovery and sets system clock (`date -s`) before strict certificate validation. |
| `/opt/luaworks/tasks/harmonywebservices/proxy/accountmanager.lua` | `26,154 B` | `26,137 B` | `-17 B` | Minor account proxy bytecode update. |
| `/opt/luaworks/tasks/activityengine/core/timemanager.lua` | `9,222 B` | `9,221 B` | `-1 B` | Changed time endpoint request method from `POST` to `GET`. |
| `/opt/luaworks/tasks/connectserver/plugins/ssdp.lua` | `67,054 B` | `62,559 B` | `-4,495 B` | Removed Belkin WeMo and EchoStar/DISH Hopper & Joey SSDP/SOAP discovery handlers. |
| `/opt/luaworks/tasks/harmonyengine/apihandler/activity.lua` | `95,844 B` | `95,824 B` | `-20 B` | Removed `Hopper` special-case reference. |
| `/opt/luaworks/tasks/harmonyengine/core/ipmanager.lua` | `32,649 B` | `32,609 B` | `-40 B` | Removed `hopper` reference in IP device manager. |
| `/opt/luaworks/tasks/harmonyengine/plugins/sonosws.lua` | `59,155 B` | `59,323 B` | `+168 B` | Migrated Sonos local WebSocket TLS client to `sslcontextclient` (`wolfSSL`). |
| `/opt/luaworks/tasks/harmonyengine/plugins/sonosbrownie.lua` | `102,911 B` | `102,831 B` | `-80 B` | Minor Sonos plugin bytecode cleanup. |
